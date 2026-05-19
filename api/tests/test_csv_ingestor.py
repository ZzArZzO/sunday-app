from decimal import Decimal

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


def test_ingest_skips_unsupported_rows(db: Session) -> None:
    portfolio = _seed_user_and_portfolio(db)
    csv = (
        "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
        "2024-01-15,sell,VWCE,IE00BK5BQT80,etf,1,100.00,1.00\n"
        "2024-01-15,buy,VWCE,IE00BK5BQT80,etf,1,100.00,1.00\n"
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv)

    assert result.rows_read == 2
    assert result.lots_created == 1
    assert any("sell" in w for w in result.warnings)
