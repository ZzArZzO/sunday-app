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


# Trade Republic's current "Transaction export" download -- no literal "isin"
# column (it's inside `symbol`), `name` carries the human-readable instrument
# name. Regression coverage for a real export that silently dropped every
# ISIN and produced wordy tickers like "CORE S&P 500 USD (ACC)" before the
# dedicated column map (see TRADE_REPUBLIC_V2_HEADER_ALIASES).
TR_V2_HEADER = (
    "datetime,date,account_type,category,type,asset_class,name,symbol,shares,"
    "price,amount,fee,tax,currency,original_amount,original_currency,fx_rate,"
    "description,transaction_id,counterparty_name,counterparty_iban,"
    "payment_reference,mcc_code\n"
)
TR_V2_CSV = TR_V2_HEADER + (
    '"2024-10-16T11:24:11Z","2024-10-16","DEFAULT","CASH","CUSTOMER_INBOUND","","A. Costa","","","","100.00","","","EUR","","","","","1","","","",""\n'
    '"2024-10-17T10:27:08Z","2024-10-17","DEFAULT","TRADING","BUY","STOCK","ASML","NL0010273215","0.155333","630.90","-98.00","-1.00","","EUR","","","","","2","","","",""\n'
    '"2024-11-04T15:09:10Z","2024-11-04","DEFAULT","TRADING","BUY","FUND","Core S&P 500 USD (Acc)","IE00B5BMR087","0.044951","556.16","-25.00","","","EUR","","","","","3","","","",""\n'
    '"2024-11-16T14:50:05Z","2024-11-16","DEFAULT","TRADING","SELL","STOCK","ASML","NL0010273215","0.05","700.00","35.00","-1.00","","EUR","","","","","4","","","",""\n'
    '"2024-11-07T13:45:16Z","2024-11-07","DEFAULT","CASH","DIVIDEND","STOCK","ASML","NL0010273215","0.759197","","0.98","","","EUR","","","","","5","","","",""\n'
)


def test_trade_republic_v2_format_is_detected() -> None:
    fieldnames = TR_V2_HEADER.strip().split(",")
    assert csv_ingestor._detect_format(fieldnames) == "trade_republic_v2"


def test_trade_republic_v2_captures_isin_and_maps_fund_to_etf(db: Session) -> None:
    portfolio = _seed(db)

    result = csv_ingestor.ingest_csv(db, portfolio, TR_V2_CSV)

    # 5 rows total; the CASH inbound transfer is skipped (not a position event).
    assert result.rows_read == 5
    assert any("CUSTOMER_INBOUND" in w for w in result.warnings)
    asml = next(p for p in portfolio.positions if p.ticker == "ASML")
    fund = next(p for p in portfolio.positions if "CORE S&P 500" in p.ticker)
    assert asml.isin == "NL0010273215"
    assert asml.asset_class == "stock"
    assert fund.isin == "IE00B5BMR087"
    assert fund.asset_class == "etf"  # TR's "FUND" normalised to Sunday's "etf"
    assert result.positions_created == 2  # ASML + the fund


def test_trade_republic_v2_crypto_uses_short_symbol_not_full_name(db: Session) -> None:
    """TR's crypto rows invert the usual columns: `symbol` holds the actual
    trading symbol ("ADA") and `name` holds the full name ("Cardano") -- the
    opposite of stock rows, where `symbol` is the ISIN. Getting this backwards
    means pricing tries to look up "CARDANO-EUR", which doesn't exist."""
    portfolio = _seed(db)
    csv_text = TR_V2_HEADER + (
        '"2024-11-25T13:22:02Z","2024-11-25","DEFAULT","TRADING","BUY","CRYPTO","Cardano","ADA","51.513412","0.969777","-49.96","-1.00","","EUR","","","","","6","","","",""\n'
    )

    result = csv_ingestor.ingest_csv(db, portfolio, csv_text)

    assert result.rows_read == 1
    ada = portfolio.positions[0]
    assert ada.ticker == "ADA"
    assert ada.isin is None
    assert ada.asset_class == "crypto"
