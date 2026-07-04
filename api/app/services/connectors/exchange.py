"""Read-only exchange connector (CCXT).

Connect a centralized exchange with a *read-only* API key (no trading, no
withdrawals) and snapshot its current balances as holdings — same privacy stance
as the address connector: we read, never move funds. Like a snapshot, balances
have no cost-basis history, so re-syncing replaces this connection's holdings.

Credentials are encrypted at rest (see secrets.py). The connector is dormant
unless `ccxt` is installed AND `connection_secret_key` is set (graceful
degradation, mirroring the billing/LLM/email tiers).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from sqlalchemy.orm import Session

from app.models import Connection, Portfolio
from app.services.connectors import secrets
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

# Launch set. CCXT supports far more; these are the ones we surface + test against.
# Bitvavo is the EUR-native EU leader (dominant in NL, growing in DE); Kraken /
# Coinbase / Binance round out the set EU retail actually uses. All are CCXT ids.
SUPPORTED_EXCHANGES = {"bitvavo", "kraken", "coinbase", "binance"}


def is_supported(exchange: str) -> bool:
    return exchange.strip().lower() in SUPPORTED_EXCHANGES


@runtime_checkable
class ExchangeFetcher(Protocol):
    """Reads current balances for one exchange account (read-only credentials)."""

    def fetch_balances(self, exchange: str, api_key: str, api_secret: str) -> list[TokenBalance]: ...


class CcxtFetcher:
    """Fetches balances via CCXT. Lazy-imports ccxt so the dep stays optional."""

    def fetch_balances(self, exchange: str, api_key: str, api_secret: str) -> list[TokenBalance]:
        try:
            import ccxt
        except ImportError as exc:  # pragma: no cover - depends on optional dep
            raise ConnectorNotConfigured("ccxt is required for exchange sync") from exc

        klass = getattr(ccxt, exchange.strip().lower(), None)
        if klass is None:
            raise ConnectorNotConfigured(f"ccxt has no exchange {exchange!r}")

        client = klass({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
        balances = client.fetch_balance()
        totals = balances.get("total", {}) if isinstance(balances, dict) else {}

        out: list[TokenBalance] = []
        for symbol, amount in totals.items():
            qty = to_decimal(amount)
            if not symbol or qty is None or qty <= 0:
                continue
            # Price enrichment is left to the app's existing price layer; the
            # snapshot only needs quantities to value via live prices.
            out.append(TokenBalance(symbol=str(symbol), quantity=qty))
        return out


def get_fetcher() -> ExchangeFetcher | None:
    """The exchange fetcher, or None when exchange sync is disabled (no ccxt / no key)."""
    if not secrets.is_configured():
        return None
    try:
        import ccxt  # noqa: F401
    except ImportError:
        return None
    return CcxtFetcher()


@dataclass
class ExchangeConnector:
    """An `ImportSource` over one exchange account."""

    exchange: str
    api_key: str
    api_secret: str
    fetcher: ExchangeFetcher
    kind: str = "exchange"

    def fetch(self) -> list[CanonicalTransaction]:
        balances = self.fetcher.fetch_balances(self.exchange, self.api_key, self.api_secret)
        return snapshot_to_transactions(balances)


def store_credentials(api_key: str, api_secret: str) -> str:
    """Encrypt exchange credentials into the blob stored on `Connection.secret_enc`."""
    return secrets.encrypt(json.dumps({"api_key": api_key, "api_secret": api_secret}))


def _load_credentials(connection: Connection) -> tuple[str, str]:
    if not connection.secret_enc:
        raise ConnectorNotConfigured("connection has no stored credentials")
    data = json.loads(secrets.decrypt(connection.secret_enc))
    return data["api_key"], data["api_secret"]


def sync_exchange(
    db: Session,
    portfolio: Portfolio,
    connection: Connection,
    *,
    fetcher: ExchangeFetcher,
    max_holdings: int | None = None,
) -> ApplyResult:
    """Fetch the exchange account's balances and replace this connection's holdings.

    On failure the connection is marked `error` and the exception re-raised for
    the route to translate.
    """
    exchange = str(connection.config.get("exchange", ""))
    api_key, api_secret = _load_credentials(connection)
    connector = ExchangeConnector(
        exchange=exchange, api_key=api_key, api_secret=api_secret, fetcher=fetcher
    )

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
