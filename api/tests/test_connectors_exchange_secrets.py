"""Exchange credential encryption + full DB sync.

Gated on the optional `cryptography` dep — the whole module skips cleanly when
it's absent, so the core connector tests (test_connectors_exchange.py) still run.
"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Connection, Lot, Portfolio, User
from app.services.connectors import exchange as ex
from app.services.connectors.snapshot import TokenBalance

crypto = pytest.importorskip("cryptography.fernet")


class FakeFetcher:
    def __init__(self, balances: list[TokenBalance]) -> None:
        self._balances = balances

    def fetch_balances(self, exchange: str, api_key: str, api_secret: str) -> list[TokenBalance]:
        return self._balances


def _seed(db: Session) -> Portfolio:
    user = User(id=1, email="demo@test.local")
    db.add(user)
    db.flush()
    portfolio = Portfolio(user_id=user.id, name="Main")
    db.add(portfolio)
    db.flush()
    user.portfolios.append(portfolio)
    return portfolio


@pytest.fixture()
def secret_key(monkeypatch) -> str:
    from app.config import get_settings

    key = crypto.Fernet.generate_key().decode()
    monkeypatch.setattr(get_settings(), "connection_secret_key", key)
    return key


def test_store_and_load_credentials_roundtrip(secret_key) -> None:
    blob = ex.store_credentials("my-key", "my-secret")
    assert "my-secret" not in blob  # encrypted, not plaintext
    conn = Connection(portfolio_id=1, kind="exchange", label="Kraken", config={"exchange": "kraken"})
    conn.secret_enc = blob
    assert ex._load_credentials(conn) == ("my-key", "my-secret")


def test_sync_exchange_replaces_holdings(db: Session, secret_key) -> None:
    portfolio = _seed(db)
    conn = Connection(
        portfolio_id=portfolio.id, kind="exchange", label="Kraken", config={"exchange": "kraken"}
    )
    conn.secret_enc = ex.store_credentials("k", "s")
    db.add(conn)
    db.flush()
    portfolio.connections.append(conn)

    ex.sync_exchange(db, portfolio, conn, fetcher=FakeFetcher([TokenBalance("BTC", Decimal("0.5"))]))
    btc = next(p for p in portfolio.positions if p.ticker == "BTC")
    assert btc.quantity == Decimal("0.50000000")
    assert conn.status == "active"

    ex.sync_exchange(db, portfolio, conn, fetcher=FakeFetcher([TokenBalance("BTC", Decimal("0.8"))]))
    db.refresh(btc)
    assert btc.quantity == Decimal("0.80000000")
    assert db.query(Lot).filter(Lot.connection_id == conn.id).count() == 1
