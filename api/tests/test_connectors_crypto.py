"""Tests for the read-only crypto address connector (services/connectors/crypto_address).

Uses a fake balance provider — no network. Covers validation, balance mapping,
the snapshot→canonical-transaction translation, and live re-sync (replace) +
error handling, which is what the route relies on.
"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Connection, Lot, Portfolio, User
from app.services.connectors import crypto_address as ca


class FakeProvider:
    def __init__(self, balances: list[ca.TokenBalance], *, fail: bool = False) -> None:
        self._balances = balances
        self._fail = fail

    def fetch_balances(self, address: str) -> list[ca.TokenBalance]:
        if self._fail:
            raise RuntimeError("indexer down")
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


def _addr_conn(db: Session, portfolio: Portfolio, address: str) -> Connection:
    conn = Connection(
        portfolio_id=portfolio.id, kind="address", label="wallet", config={"address": address}
    )
    db.add(conn)
    db.flush()
    portfolio.connections.append(conn)
    return conn


def test_evm_address_validation() -> None:
    assert ca.is_valid_evm_address("0x" + "a" * 40)
    assert not ca.is_valid_evm_address("0x123")
    assert not ca.is_valid_evm_address("not-an-address")


def test_short_address() -> None:
    assert ca.short_address("0xabcdef1234567890abcdef1234567890abcdef12") == "0xabcd…ef12"


def test_parse_balances_skips_bad_rows() -> None:
    payload = {
        "balances": [
            {"symbol": "ETH", "amount": "1.5", "price_eur": "1500"},
            {"symbol": "", "amount": "9"},  # no symbol → skip
            {"symbol": "BAD", "amount": "x"},  # unparseable amount → skip
            {"symbol": "SOL", "amount": "10", "price_eur": "bad"},  # price ignored, kept
        ]
    }
    out = ca._parse_balances(payload)
    assert [b.symbol for b in out] == ["ETH", "SOL"]
    assert out[0].price_eur == Decimal("1500")
    assert out[1].price_eur is None


def test_connector_builds_buys_and_skips_zero() -> None:
    provider = FakeProvider(
        [
            ca.TokenBalance("ETH", Decimal("2"), Decimal("1500")),
            ca.TokenBalance("DUST", Decimal("0")),
        ]
    )
    txns = ca.AddressConnector(address="0x" + "a" * 40, provider=provider).fetch()
    assert len(txns) == 1
    assert txns[0].ticker == "ETH"
    assert txns[0].asset_class == "crypto"
    assert txns[0].kind == "buy"


def test_get_provider_disabled_without_key() -> None:
    # Default settings have no crypto_indexer_api_key → address sync is dormant.
    assert ca.get_provider() is None


def test_sync_creates_then_replaces_holdings(db: Session) -> None:
    portfolio = _seed(db)
    conn = _addr_conn(db, portfolio, "0x" + "a" * 40)

    ca.sync_address(
        db, portfolio, conn, provider=FakeProvider([ca.TokenBalance("ETH", Decimal("2"), Decimal("1500"))])
    )
    eth = next(p for p in portfolio.positions if p.ticker == "ETH")
    assert eth.quantity == Decimal("2.00000000")
    assert conn.status == "active"
    assert conn.last_synced_at is not None

    # Wallet moved to 5 ETH — re-sync replaces rather than stacks.
    ca.sync_address(
        db, portfolio, conn, provider=FakeProvider([ca.TokenBalance("ETH", Decimal("5"), Decimal("1600"))])
    )
    db.refresh(eth)
    assert eth.quantity == Decimal("5.00000000")
    assert db.query(Lot).filter(Lot.connection_id == conn.id).count() == 1


def test_sync_marks_connection_error_on_failure(db: Session) -> None:
    portfolio = _seed(db)
    conn = _addr_conn(db, portfolio, "0x" + "a" * 40)

    with pytest.raises(RuntimeError):
        ca.sync_address(db, portfolio, conn, provider=FakeProvider([], fail=True))

    assert conn.status == "error"
    assert conn.error_detail is not None
