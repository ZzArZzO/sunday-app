"""Read-only crypto address connector.

Paste a *public* wallet address; we read its current token balances from an
indexer and snapshot them as holdings. No private keys, no signing, no custody —
it's reading a public ledger, which keeps the privacy promise intact.

Live balances are a *snapshot*, not a transaction history, so each token becomes
one buy-like lot and re-syncing replaces the connection's holdings (see
`replace_connection_lots`). The connector is dormant until an indexer key is
configured (graceful degradation, like the LLM/email/billing tiers).

Launch chains are **EVM** (Ethereum + L2s, `0x…`) and **Solana** (base58). A
single `ZerionBalanceProvider` covers both — Zerion's `/positions` endpoint
routes by address, so one vendor + one call serves every launch chain. The
generic `HttpBalanceProvider` is kept as a vendor-agnostic fallback (set
`CRYPTO_INDEXER_PROVIDER=http` to use it).

When a `ZerionTransactionProvider` is supplied, each token's balance is split
into its real acquisition lots (FIFO, via `lot_history`) so the crypto tax
holding-period clock has true purchase dates. Without it, or on a history fetch
failure, the connector falls back to a single `now`-dated snapshot lot.
"""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Connection, Portfolio
from app.services.connectors.base import (
    ApplyResult,
    CanonicalTransaction,
    ConnectorNotConfigured,
    replace_connection_lots,
)
from app.services.connectors.lot_history import (
    LedgerEvent,
    balances_to_dated_transactions,
)
from app.services.connectors.snapshot import (
    TokenBalance,
    snapshot_to_transactions,
    to_decimal,
)

log = logging.getLogger(__name__)

__all__ = [
    "TokenBalance",
    "LedgerEvent",
    "AddressConnector",
    "BalanceProvider",
    "HttpBalanceProvider",
    "ZerionBalanceProvider",
    "TransactionProvider",
    "ZerionTransactionProvider",
    "get_provider",
    "get_tx_provider",
    "is_valid_address",
    "is_valid_evm_address",
    "is_valid_solana_address",
    "normalize_address",
    "short_address",
    "sync_address",
]

# EVM address: 0x followed by 40 hex chars (case-insensitive).
_EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# Solana address: base58-encoded 32-byte public key. Base58 excludes 0/O/I/l;
# lengths run ~32-44 chars. Case-sensitive — never lowercase a Solana address.
_SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def is_valid_evm_address(address: str) -> bool:
    return bool(_EVM_ADDRESS_RE.match(address.strip()))


def is_valid_solana_address(address: str) -> bool:
    return bool(_SOLANA_ADDRESS_RE.match(address.strip()))


def normalize_address(address: str) -> tuple[str, str] | None:
    """Return ``(canonical_address, chain)`` or ``None`` if unrecognised.

    EVM addresses are case-insensitive, so they're lowercased for stable dedup.
    Solana base58 addresses are case-sensitive and returned verbatim. ``chain``
    is ``"evm"`` or ``"solana"``.
    """
    a = address.strip()
    if is_valid_evm_address(a):
        return a.lower(), "evm"
    if is_valid_solana_address(a):
        return a, "solana"
    return None


def is_valid_address(address: str) -> bool:
    return normalize_address(address) is not None


def short_address(address: str) -> str:
    a = address.strip()
    return f"{a[:6]}…{a[-4:]}" if len(a) > 12 else a


@runtime_checkable
class BalanceProvider(Protocol):
    """Reads current token balances for a public address from some indexer."""

    def fetch_balances(self, address: str) -> list[TokenBalance]: ...


class HttpBalanceProvider:
    """Calls a configurable indexer HTTP endpoint.

    Expects JSON shaped like:
        {"balances": [{"symbol": "ETH", "amount": "1.5", "price_eur": "1500"}]}
    Adjust the request + mapping to match the chosen vendor's API.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def fetch_balances(self, address: str) -> list[TokenBalance]:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - httpx is installed
            raise ConnectorNotConfigured("httpx is required for address sync") from exc

        resp = httpx.get(
            f"{self._base_url}/balances",
            params={"address": address},
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        return _parse_balances(payload)


def _parse_balances(payload: dict) -> list[TokenBalance]:
    out: list[TokenBalance] = []
    for raw in payload.get("balances", []):
        symbol = str(raw.get("symbol", "")).strip().upper()
        qty = to_decimal(raw.get("amount", "0"))
        if not symbol or qty is None:
            continue
        out.append(TokenBalance(symbol=symbol, quantity=qty, price_eur=to_decimal(raw.get("price_eur"))))
    return out


# Page through at most this many Zerion pages (100 rows each). A safety bound so
# a pathological wallet can't loop forever; 50 pages = 5,000 rows.
_MAX_ZERION_PAGES = 50


def _zerion_paged_data(url: str, params: dict, headers: dict) -> list[dict]:
    """Collect ``data`` across all Zerion pages, following ``links.next``.

    Zerion caps a page at 100 rows and returns newest-first, so WITHOUT paging the
    oldest rows (the original acquisitions, and holdings past the 100th) are
    silently dropped — which would reset the tax clock. The ``next`` link is a full
    URL that already encodes the cursor + params, so later requests send no params.
    """
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - httpx is installed
        raise ConnectorNotConfigured("httpx is required for address sync") from exc

    data: list[dict] = []
    next_url: str | None = url
    next_params: dict | None = params
    for _ in range(_MAX_ZERION_PAGES):
        if next_url is None:
            break
        resp = httpx.get(next_url, params=next_params, headers=headers, timeout=20.0)
        resp.raise_for_status()
        payload = resp.json()
        data.extend(payload.get("data") or [])
        next_url = (payload.get("links") or {}).get("next")
        next_params = None  # the next link already carries currency/filters/cursor
    return data


class ZerionBalanceProvider:
    """Reads a wallet's current token balances from the Zerion API.

    One endpoint serves both EVM and Solana wallets (Zerion routes by address),
    so a single provider covers the launch chains. Values are requested directly
    in EUR. Auth is HTTP Basic with the API key as the username and an empty
    password, per Zerion's docs.

        GET {base_url}/wallets/{address}/positions/
            ?currency=eur&filter[positions]=only_simple&filter[trash]=only_non_trash
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _auth_header(self) -> str:
        token = base64.b64encode(f"{self._api_key}:".encode()).decode()
        return f"Basic {token}"

    def fetch_balances(self, address: str) -> list[TokenBalance]:
        data = _zerion_paged_data(
            f"{self._base_url}/wallets/{address}/positions/",
            {
                "currency": "eur",
                "filter[positions]": "only_simple",  # wallet balances, not complex DeFi legs
                "filter[trash]": "only_non_trash",  # drop spam/airdropped tokens
                "page[size]": 100,
            },
            {"Authorization": self._auth_header(), "accept": "application/json"},
        )
        return _parse_zerion({"data": data})


def _parse_zerion(payload: dict) -> list[TokenBalance]:
    """Map a Zerion ``/positions`` response → TokenBalances, skipping unusable rows.

    Each position carries ``attributes.fungible_info.symbol``, a
    ``attributes.quantity.float`` magnitude, and a per-unit ``attributes.price``
    already in the requested currency (EUR).
    """
    out: list[TokenBalance] = []
    for item in payload.get("data", []):
        attrs = item.get("attributes", {}) if isinstance(item, dict) else {}
        info = attrs.get("fungible_info") or {}
        symbol = str(info.get("symbol", "")).strip().upper()
        qty = to_decimal((attrs.get("quantity") or {}).get("float"))
        if not symbol or qty is None:
            continue
        out.append(TokenBalance(symbol=symbol, quantity=qty, price_eur=to_decimal(attrs.get("price"))))
    return out


def get_provider() -> BalanceProvider | None:
    """The configured balance provider, or None when address sync is disabled.

    Selects by ``CRYPTO_INDEXER_PROVIDER`` (default ``zerion``); ``http`` falls
    back to the vendor-agnostic `HttpBalanceProvider`.
    """
    settings = get_settings()
    if not settings.crypto_indexer_api_key:
        return None
    provider = (settings.crypto_indexer_provider or "zerion").strip().lower()
    if provider == "http":
        return HttpBalanceProvider(settings.crypto_indexer_base_url, settings.crypto_indexer_api_key)
    return ZerionBalanceProvider(settings.crypto_indexer_base_url, settings.crypto_indexer_api_key)


@runtime_checkable
class TransactionProvider(Protocol):
    """Reads a wallet's transfer history, grouped by token symbol, for FIFO lot
    reconstruction. Optional — absence means snapshot-only (no real lot dates)."""

    def fetch_transactions(self, address: str) -> dict[str, list[LedgerEvent]]: ...


class ZerionTransactionProvider:
    """Reads transfer history from the Zerion API for FIFO lot dating.

        GET {base_url}/wallets/{address}/transactions/?currency=eur

    Each transaction has a ``mined_at`` time and a list of ``transfers``; a
    transfer's ``direction`` (``in``/``out``) is the acquire/dispose signal.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _auth_header(self) -> str:
        token = base64.b64encode(f"{self._api_key}:".encode()).decode()
        return f"Basic {token}"

    def fetch_transactions(self, address: str) -> dict[str, list[LedgerEvent]]:
        data = _zerion_paged_data(
            f"{self._base_url}/wallets/{address}/transactions/",
            {
                "currency": "eur",
                "filter[trash]": "only_non_trash",  # match /positions; exclude spam transfers
                "page[size]": 100,
            },
            {"Authorization": self._auth_header(), "accept": "application/json"},
        )
        return _parse_zerion_transactions({"data": data})


def _zerion_timestamp(value: object) -> datetime | None:
    """Parse Zerion ``mined_at`` (a unix epoch or an ISO-8601 string) → UTC."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _parse_zerion_transactions(payload: dict) -> dict[str, list[LedgerEvent]]:
    """Map a Zerion ``/transactions`` response → {symbol: [LedgerEvent]}.

    One event per fungible transfer; ``direction`` in/out drives acquire/dispose.
    Rows without a symbol, quantity, or parseable time are skipped.

    History is keyed by token symbol, which matches how `/positions` aggregates a
    fungible's balance across chains. The trash filter on the request excludes
    impersonation/spam tokens that share a real symbol; the residual risk is two
    *non-trash* assets with the same ticker merging — a rare correctness edge that
    would need contract-level keying to fully close.
    """
    history: dict[str, list[LedgerEvent]] = {}
    for item in payload.get("data", []):
        attrs = item.get("attributes", {}) if isinstance(item, dict) else {}
        date = _zerion_timestamp(attrs.get("mined_at"))
        if date is None:
            continue
        for transfer in attrs.get("transfers", []) or []:
            info = transfer.get("fungible_info") or {}
            symbol = str(info.get("symbol", "")).strip().upper()
            qty = to_decimal((transfer.get("quantity") or {}).get("float"))
            direction = str(transfer.get("direction", "")).strip().lower()
            if not symbol or qty is None or qty <= 0 or direction not in ("in", "out"):
                continue
            history.setdefault(symbol, []).append(
                LedgerEvent(
                    date=date,
                    acquire=(direction == "in"),
                    quantity=qty,
                    unit_price_eur=to_decimal(transfer.get("price")),
                )
            )
    return history


def get_tx_provider() -> TransactionProvider | None:
    """The configured transaction provider, or None when unavailable.

    Only Zerion supplies history; the generic ``http`` indexer doesn't, so the
    connector stays on snapshot dating there.
    """
    settings = get_settings()
    if not settings.crypto_indexer_api_key:
        return None
    if (settings.crypto_indexer_provider or "zerion").strip().lower() != "zerion":
        return None
    return ZerionTransactionProvider(settings.crypto_indexer_base_url, settings.crypto_indexer_api_key)


@dataclass
class AddressConnector:
    """An `ImportSource` over a public wallet address."""

    address: str
    provider: BalanceProvider
    kind: str = "address"

    def fetch(self) -> list[CanonicalTransaction]:
        return snapshot_to_transactions(self.provider.fetch_balances(self.address))


def sync_address(
    db: Session,
    portfolio: Portfolio,
    connection: Connection,
    *,
    provider: BalanceProvider,
    tx_provider: TransactionProvider | None = None,
    max_holdings: int | None = None,
) -> ApplyResult:
    """Fetch the address's current balances and replace this connection's holdings.

    With a `tx_provider`, each token is split into FIFO-reconstructed lots so the
    tax holding-period clock has real purchase dates; without it (or if history
    fetch fails) it falls back to a single `now`-dated snapshot lot. A
    provider/parse failure on the *balance* read marks the connection `error` and
    re-raises for the route to translate.
    """
    address = str(connection.config.get("address", ""))

    try:
        balances = provider.fetch_balances(address)
        if tx_provider is None:
            txns = snapshot_to_transactions(balances)
        else:
            now = datetime.now(timezone.utc)
            try:
                history = tx_provider.fetch_transactions(address)
            except Exception as exc:  # noqa: BLE001 - history is best-effort
                log.warning(
                    "Transaction history failed for %s (using snapshot dates): %s",
                    short_address(address),
                    exc,
                )
                history = {}
            txns = balances_to_dated_transactions(balances, history, now=now)
    except Exception as exc:
        connection.status = "error"
        connection.error_detail = str(exc)[:500]
        db.commit()
        raise

    result = replace_connection_lots(db, portfolio, connection, txns, max_holdings=max_holdings)

    connection.status = "active"
    connection.error_detail = None
    connection.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return result
