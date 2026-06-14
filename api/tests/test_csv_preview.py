"""Tests for the parse-only CSV preview (services/csv_ingestor.preview_csv).

Pure: no DB. Verifies column detection and per-row ok/skipped status.
"""

from app.services import csv_ingestor

_NATIVE = (
    "date,type,ticker,isin,asset_class,quantity,unit_price_eur,fees_eur\n"
    "2026-01-02,buy,AAPL,US0378331005,stock,10,150.00,1.00\n"
    "2026-02-02,sell,AAPL,US0378331005,stock,4,170.00,1.00\n"
    "2026-03-02,wibble,AAPL,US0378331005,stock,1,1.00,0\n"  # unsupported type → skipped
)


def test_preview_detects_format_and_columns():
    result = csv_ingestor.preview_csv(_NATIVE)
    assert result.detected_format == "sunday_native"
    mapped = {c.mapped_to for c in result.columns}
    assert {"date", "type", "ticker", "quantity"}.issubset(mapped)
    # Samples come from the first data row.
    ticker_col = next(c for c in result.columns if c.mapped_to == "ticker")
    assert ticker_col.sample == "AAPL"


def test_preview_marks_ok_and_skipped_rows():
    result = csv_ingestor.preview_csv(_NATIVE)
    assert result.ok_count == 2
    assert result.skipped_count == 1
    skipped = [r for r in result.rows if r.status == "skipped"]
    assert len(skipped) == 1
    assert skipped[0].reason and "unsupported type" in skipped[0].reason.lower()
    # First data row is line 2.
    assert result.rows[0].line == 2 and result.rows[0].status == "ok"
    assert result.rows[0].ticker == "AAPL"


def test_preview_empty_csv():
    result = csv_ingestor.preview_csv("")
    assert result.ok_count == 0
    assert result.warnings
