"""Tests for the provider-agnostic connector core (services/connectors/base).

Covers what CSV ingest exercises indirectly but the live connectors will rely on
directly: lots tagged with their originating Connection, the free-tier holdings
cap, and live re-sync (replace-this-source's-holdings) semantics.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Connection, Lot, Portfolio, User
from app.services.connectors import base


def _seed_portfolio(db: Session) -> Portfolio:
    user = User(id=1, email="demo@test.local")
    db.add(user)
    db.flush()
    portfolio = Portfolio(user_id=user.id, name="Main")
    db.add(portfolio)
    db.flush()
    user.portfolios.append(portfolio)
    return portfolio


def _conn(db: Session, portfolio: Portfolio, kind: str, label: str) -> Connection:
    conn = Connection(portfolio_id=portfolio.id, kind=kind, label=label)
    db.add(conn)
    db.flush()
    portfolio.connections.append(conn)
    return conn


def _buy(ticker: str, qty: str, price: str, *, asset_class: str = "crypto") -> base.CanonicalTransaction:
    return base.CanonicalTransaction(
        date=datetime(2024, 1, 1),
        kind=base.KIND_BUY,
        ticker=ticker,
        isin=None,
        asset_class=asset_class,
        quantity=Decimal(qty),
        unit_price_eur=Decimal(price),
        fees_eur=Decimal("0"),
    )


def test_apply_tags_lots_with_connection(db: Session) -> None:
    portfolio = _seed_portfolio(db)
    conn = _conn(db, portfolio, "address", "0xabc…")

    result = base.apply_transactions(
        db, portfolio, [_buy("ETH", "2", "1500")], source_label="conn:test", connection=conn
    )

    assert result.positions_created == 1
    assert result.lots_created == 1
    lot = db.query(Lot).one()
    assert lot.connection_id == conn.id
    assert lot.source == "conn:test"


def test_holdings_cap_rolls_back(db: Session) -> None:
    portfolio = _seed_portfolio(db)
    txns = [_buy("ETH", "2", "1500"), _buy("BTC", "0.1", "40000")]

    with pytest.raises(base.HoldingsLimitExceeded) as exc:
        base.apply_transactions(db, portfolio, txns, max_holdings=1)

    assert exc.value.limit == 1
    assert exc.value.attempted == 2


def test_replace_connection_lots_resyncs_holdings(db: Session) -> None:
    portfolio = _seed_portfolio(db)
    conn = _conn(db, portfolio, "address", "0xabc…")

    base.apply_transactions(
        db, portfolio, [_buy("ETH", "2", "1500")], connection=conn
    )
    eth = next(p for p in portfolio.positions if p.ticker == "ETH")
    assert eth.quantity == Decimal("2.00000000")

    # Wallet now holds 5 ETH — a re-sync should replace, not stack on top.
    base.replace_connection_lots(
        db, portfolio, conn, [_buy("ETH", "5", "1500")]
    )

    db.refresh(eth)
    assert eth.quantity == Decimal("5.00000000")
    assert db.query(Lot).filter(Lot.connection_id == conn.id).count() == 1


def test_replace_to_empty_zeroes_position(db: Session) -> None:
    portfolio = _seed_portfolio(db)
    conn = _conn(db, portfolio, "address", "0xabc…")
    base.apply_transactions(db, portfolio, [_buy("SOL", "10", "100")], connection=conn)

    base.replace_connection_lots(db, portfolio, conn, [])

    sol = next(p for p in portfolio.positions if p.ticker == "SOL")
    db.refresh(sol)
    assert sol.quantity == Decimal("0E-8")
