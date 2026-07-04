from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Connection, Portfolio, User
from app.services import csv_ingestor

SAMPLE_CSV = (
    "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
    "2024-01-15,buy,VWCE,IE00BK5BQT80,etf,10,100.00,1.00\n"
    "2024-02-15,buy,VWCE,IE00BK5BQT80,etf,10,120.00,1.00\n"
    "2024-03-01,buy,BTC,,crypto,0.05,40000.00,0.00\n"
)


def _seed_user_and_portfolio(db: Session) -> Portfolio:
    user = User(id=1, email="demo@test.local")
    db.add(user)
    db.flush()
    portfolio = Portfolio(user_id=user.id, name="Main")
    db.add(portfolio)
    db.flush()
    user.portfolios.append(portfolio)
    return portfolio


def test_ingest_creates_positions_and_lots(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)

    result = csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV)

    assert result.rows_read == 3
    assert result.positions_created == 2
    assert result.positions_updated == 1
    assert result.lots_created == 3
    assert result.warnings == []


def test_ingest_computes_weighted_avg_cost(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV)

    vwce = next(p for p in portfolio.positions if p.ticker == "VWCE")

    # 10 @ 100 + 10 @ 120 + 2 fees → (1000 + 1200 + 2) / 20 = 110.10
    assert vwce.quantity == Decimal("20.00000000")
    assert vwce.avg_cost_eur == Decimal("110.1000")


def test_sell_reduces_quantity_and_keeps_avg_cost(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    csv = (
        "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
        "2024-01-15,buy,VWCE,IE00BK5BQT80,etf,10,100.00,0.00\n"
        "2024-02-15,sell,VWCE,IE00BK5BQT80,etf,3,150.00,0.00\n"
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv)
    vwce = next(p for p in portfolio.positions if p.ticker == "VWCE")

    # EU average-cost: qty drops, avg cost is unchanged by a sale.
    assert vwce.quantity == Decimal("7.00000000")
    assert vwce.avg_cost_eur == Decimal("100.0000")
    assert result.lots_created == 1  # only the buy is a lot
    assert any("sell" in w for w in result.warnings)


def test_oversell_clamps_to_zero(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    csv = (
        "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
        "2024-01-15,buy,VWCE,IE00BK5BQT80,etf,5,100.00,0.00\n"
        "2024-02-15,sell,VWCE,IE00BK5BQT80,etf,10,150.00,0.00\n"
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv)
    vwce = next(p for p in portfolio.positions if p.ticker == "VWCE")

    assert vwce.quantity == Decimal("0.00000000")
    assert any("CLAMPED" in w for w in result.warnings)


def test_dividend_does_not_change_holdings(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    csv = (
        "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
        "2024-01-15,buy,VWCE,IE00BK5BQT80,etf,10,100.00,0.00\n"
        "2024-03-01,dividend,VWCE,IE00BK5BQT80,etf,,,0.00\n"
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv)
    vwce = next(p for p in portfolio.positions if p.ticker == "VWCE")

    assert vwce.quantity == Decimal("10.00000000")
    assert vwce.avg_cost_eur == Decimal("100.0000")
    assert result.lots_created == 1
    assert any("dividend" in w for w in result.warnings)


def test_split_with_ratio_scales_qty_and_avg(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    csv = (
        "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur,split_ratio\n"
        "2024-01-15,buy,AAPL,US0378331005,stock,10,100.00,0.00,\n"
        "2024-06-01,split,AAPL,US0378331005,stock,,,0.00,4\n"
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv)
    aapl = next(p for p in portfolio.positions if p.ticker == "AAPL")

    # 4-for-1 split: 10 → 40 shares, basis preserved so avg 100 → 25.
    assert aapl.quantity == Decimal("40.00000000")
    assert aapl.avg_cost_eur == Decimal("25.0000")
    assert any("split" in w for w in result.warnings)


def test_split_without_ratio_is_flagged_not_applied(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    csv = (
        "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
        "2024-01-15,buy,AAPL,US0378331005,stock,10,100.00,0.00\n"
        "2024-06-01,split,AAPL,US0378331005,stock,,,0.00\n"
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv)
    aapl = next(p for p in portfolio.positions if p.ticker == "AAPL")

    assert aapl.quantity == Decimal("10.00000000")  # unchanged — not guessed
    assert any("SPLIT_FLAGGED" in w for w in result.warnings)


def test_holdings_cap_blocks_over_limit_import(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    db.commit()  # persist the seed so the internal rollback only discards the ingest

    # SAMPLE_CSV results in 2 holdings (VWCE, BTC); a cap of 1 must block it.
    with pytest.raises(csv_ingestor.HoldingsLimitExceeded) as exc:
        csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV, max_holdings=1)

    assert exc.value.limit == 1
    assert exc.value.attempted == 2
    assert portfolio.positions == []  # rolled back — no partial import


def test_holdings_cap_allows_within_limit(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)

    result = csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV, max_holdings=2)

    assert result.positions_created == 2


def _csv_connection(db: Session, portfolio: Portfolio, label: str = "Trade Republic") -> Connection:
    conn = Connection(portfolio_id=portfolio.id, kind="csv", label=label)
    db.add(conn)
    db.flush()
    portfolio.connections.append(conn)
    return conn


class TestReimportDedup:
    """Re-uploading the same broker's CSV should replace its prior positions,
    not double them -- this reproduces the exact bug hit importing the same
    854-row Trade Republic file twice, where every quantity ended up ~2x."""

    def test_reimporting_same_csv_does_not_double_quantities(self, db: Session) -> None:
        portfolio = _seed_user_and_portfolio(db)
        conn = _csv_connection(db, portfolio)

        csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV, connection=conn)
        vwce_first = next(p for p in portfolio.positions if p.ticker == "VWCE")
        assert vwce_first.quantity == Decimal("20.00000000")

        csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV, connection=conn)
        vwce_second = next(p for p in portfolio.positions if p.ticker == "VWCE")
        assert vwce_second.quantity == Decimal("20.00000000")  # unchanged, not 40
        assert len(portfolio.positions) == 2  # VWCE + BTC, not 4

    def test_different_broker_connection_is_untouched(self, db: Session) -> None:
        """Re-importing broker A's CSV must not wipe broker B's holdings, even
        though both are 'a CSV import' -- they're different connections."""
        portfolio = _seed_user_and_portfolio(db)
        degiro_conn = _csv_connection(db, portfolio, label="DEGIRO")
        tr_conn = _csv_connection(db, portfolio, label="Trade Republic")

        degiro_csv = (
            "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
            "2024-01-01,buy,NESN,CH0038863350,stock,5,100.00,0.00\n"
        )
        csv_ingestor.ingest_csv(db, portfolio, degiro_csv, connection=degiro_conn)
        csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV, connection=tr_conn)

        nesn = next(p for p in portfolio.positions if p.ticker == "NESN")
        assert nesn.quantity == Decimal("5.00000000")  # untouched by the TR import
        assert len(portfolio.positions) == 3  # NESN + VWCE + BTC

    def test_position_with_mixed_sources_is_left_untouched(self, db: Session) -> None:
        """A position isn't fully owned by one connection (e.g. also has a
        manually-entered lot) -- don't guess, leave it alone entirely."""
        portfolio = _seed_user_and_portfolio(db)
        conn = _csv_connection(db, portfolio)

        csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV, connection=conn)
        vwce = next(p for p in portfolio.positions if p.ticker == "VWCE")
        original_quantity = vwce.quantity

        # A second, differently-sourced buy lands on the same ticker.
        manual_csv = (
            "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
            "2024-04-01,buy,VWCE,IE00BK5BQT80,etf,5,110.00,0.00\n"
        )
        csv_ingestor.ingest_csv(db, portfolio, manual_csv)  # no connection -> source="sunday_native"
        assert vwce.quantity == original_quantity + Decimal("5")

        # Re-importing the original TR connection's file must not delete VWCE
        # now that it has a mixed-source lot history -- it's excluded from the
        # replace, so the transactions apply on top of the existing pool
        # (the known, documented limitation: not a perfect reimport for a
        # ticker held across multiple sources, but never data loss).
        csv_ingestor.ingest_csv(db, portfolio, SAMPLE_CSV, connection=conn)
        assert vwce.quantity == original_quantity * 2 + Decimal("5")
