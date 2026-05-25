"""Tests for the multi-format CSV ingestor (TR auto-detect)."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Portfolio, User
from app.services import csv_ingestor

TR_NATIVE_CSV = (
    "Date,Type,Asset,ISIN,Shares,Price per share,Fee\n"
    "2024-01-15,Buy,VWCE,IE00BK5BQT80,12,98.50,1.00\n"
    "2024-02-04,Buy,BTC,,0.05,38500.00,0.00\n"
)

TR_GERMAN_CSV = (
    "Datum;Typ;Asset;ISIN;Stück;Preis pro Anteil;Gebühr\n"
    "15.01.2024;Kauf;VWCE;IE00BK5BQT80;12;98,50;1,00\n"
)


def _seed(db: Session) -> Portfolio:
    user = User(id=1, email="demo@test.local")
    db.add(user)
    db.flush()
    portfolio = Portfolio(user_id=user.id, name="Main")
    db.add(portfolio)
    db.flush()
    user.portfolios.append(portfolio)
    return portfolio


def test_tr_native_format_is_detected_and_parsed(db: Session) -> None:
    portfolio = _seed(db)

    result = csv_ingestor.ingest_csv(db, portfolio, TR_NATIVE_CSV)

    assert result.rows_read == 2
    assert result.positions_created == 2
    assert result.lots_created == 2
    vwce = next(p for p in portfolio.positions if p.ticker == "VWCE")
    btc = next(p for p in portfolio.positions if p.ticker == "BTC")
    assert vwce.asset_class == "etf"  # inferred from IE ISIN prefix
    assert btc.asset_class == "crypto"  # inferred from symbol


def test_european_decimals_and_dates_parse(db: Session) -> None:
    """Note: CSV uses ; as delimiter — Python csv defaults to ,. This case shows we
    parse what we can; semicolon-delimited files will fail header detection
    gracefully. Use a stricter dialect-sniffing pass in Phase 2."""
    portfolio = _seed(db)

    # Force a comma-delimited version of the German row
    csv_text = (
        "Datum,Typ,Asset,ISIN,Stück,Preis pro Anteil,Gebühr\n"
        '15.01.2024,Kauf,VWCE,IE00BK5BQT80,12,"98,50","1,00"\n'
    )
    result = csv_ingestor.ingest_csv(db, portfolio, csv_text)

    assert result.rows_read == 1
    vwce = next(p for p in portfolio.positions if p.ticker == "VWCE")
    assert vwce.quantity == Decimal("12.00000000")
    # avg cost = 12*98.50 + 1.00 = 1183 / 12 ≈ 98.5833
    assert vwce.avg_cost_eur == Decimal("98.5833")


def test_legacy_sunday_native_format_still_works(db: Session) -> None:
    portfolio = _seed(db)
    csv_text = (
        "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
        "2024-01-15,buy,VWCE,IE00BK5BQT80,etf,10,100.00,1.00\n"
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv_text)

    assert result.rows_read == 1
    assert result.positions_created == 1
