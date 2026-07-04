"""Tests for DEGIRO transactions import.

DEGIRO is semicolon-delimited, has no "Type" column (direction is the sign of
Quantity), exposes no symbol (Product name is the label, ISIN the identifier),
and interleaves unnamed per-amount currency columns. These tests cover delimiter
detection, sign-based direction, EUR unit cost from the Value column, and that
the noise columns + cash rows are handled.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Portfolio, User
from app.services import csv_ingestor

# Header includes the unnamed currency columns DEGIRO interleaves (the ";;").
DEGIRO_CSV = (
    "Date;Time;Product;ISIN;Reference;Venue;Quantity;Price;;Local value;;Value;;"
    "Transaction and/or third party costs;;Total;;Order ID\n"
    "02-01-2024;09:05;ASML Holding;NL0010273215;XAMS;XAMS;10;900,00;EUR;-9.000,00;EUR;-9.000,00;EUR;-3,00;EUR;-9.003,00;EUR;abc-1\n"
    "05-02-2024;10:11;ASML Holding;NL0010273215;XAMS;XAMS;5;910,00;EUR;-4.550,00;EUR;-4.550,00;EUR;-3,00;EUR;-4.553,00;EUR;abc-2\n"
    "10-03-2024;14:20;ASML Holding;NL0010273215;XAMS;XAMS;-4;950,00;EUR;3.800,00;EUR;3.800,00;EUR;-2,00;EUR;3.798,00;EUR;abc-3\n"
    "15-03-2024;00:00;EUR Withdrawal;;;;;;;;;;;;;;;;fx-1\n"
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


def test_degiro_format_detected() -> None:
    fieldnames = DEGIRO_CSV.split("\n", 1)[0].split(";")
    assert csv_ingestor._detect_format(fieldnames) == "degiro"


def test_semicolon_delimiter_detected() -> None:
    assert csv_ingestor._delimiter_for(DEGIRO_CSV) == ";"
    assert csv_ingestor._delimiter_for("a,b,c\n1,2,3\n") == ","


def test_degiro_ingest_signs_quantities_and_uses_eur_value(db: Session) -> None:
    portfolio = _seed(db)

    result = csv_ingestor.ingest_csv(db, portfolio, DEGIRO_CSV)

    assert result.rows_read == 4  # 3 trades + 1 cash row (counted, then skipped)
    assert result.positions_created == 1
    assert any("Detected format: degiro" in w for w in result.warnings)

    asml = next(p for p in portfolio.positions if p.ticker == "ASML HOLDING")
    assert asml.isin == "NL0010273215"
    assert asml.asset_class == "stock"
    # Bought 10 then 5, sold 4 → 11 held. EU average-cost: a sell leaves avg cost
    # unchanged. avg = (10*900+3 + 5*910+3) / 15 = 13556 / 15 = 903.7333.
    assert asml.quantity == Decimal("11.00000000")
    assert asml.avg_cost_eur == Decimal("903.7333")


def test_degiro_preview_reports_rows(db: Session) -> None:
    preview = csv_ingestor.preview_csv(DEGIRO_CSV)
    assert preview.detected_format == "degiro"
    assert preview.ok_count == 3  # three trades parse
    assert preview.skipped_count == 1  # the cash row has no quantity
