from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Portfolio, User
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
