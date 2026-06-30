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
"""

from __future__ import annotations

import base64
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
from app.services.connectors.snapshot import (
    TokenBalance,
    snapshot_to_transactions,
    to_decimal,
)

__all__ = [
    "TokenBalance",
    "AddressConnector",
    "BalanceProvider",
    "HttpBalanceProvider",
    "ZerionBalanceProvider",
    "get_provider",
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
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - httpx is installed
            raise ConnectorNotConfigured("httpx is required for address sync") from exc

        resp = httpx.get(
            f"{self._base_url}/wallets/{address}/positions/",
            params={
                "currency": "eur",
                "filter[positions]": "only_simple",  # wallet balances, not complex DeFi legs
                "filter[trash]": "only_non_trash",  # drop spam/airdropped tokens
                "page[size]": 100,
            },
            headers={"Authorization": self._auth_header(), "accept": "application/json"},
            timeout=20.0,
        )
        resp.raise_for_status()
        return _parse_zerion(resp.json())


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
    max_holdings: int | None = None,
) -> ApplyResult:
    """Fetch the address's current balances and replace this connection's holdings.

    On a provider/parse failure the connection is marked `error` (so the UI can
    surface it) and the exception re-raised for the route to translate.
    """
    address = str(connection.config.get("address", ""))
    connector = AddressConnector(address=address, provider=provider)

    try:
        txns = connector.fetch()
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
