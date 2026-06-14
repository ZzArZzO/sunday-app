"""Tests for the crypto holding-period clock (services/tax_summary.crypto_holding_periods).

Pure: runs over duck-typed position/lot stand-ins, no DB.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.services import tax_summary

NOW = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)


def _lot(days_ago: int, qty: str = "1"):
    return SimpleNamespace(purchased_at=NOW - timedelta(days=days_ago), quantity=Decimal(qty))


def _crypto(ticker: str, *lots):
    return SimpleNamespace(asset_class="crypto", ticker=ticker, lots=list(lots))


def test_ignores_non_crypto_positions():
    stock = SimpleNamespace(asset_class="stock", ticker="AAPL", lots=[_lot(400)])
    out = tax_summary.crypto_holding_periods([stock], now=NOW, holding_period_days=365)
    assert out == []


def test_clock_counts_down_and_flags_tax_free():
    positions = [
        _crypto("BTC", _lot(400)),  # already past 365 days → tax-free
        _crypto("ETH", _lot(100)),  # 265 days to go
    ]
    out = tax_summary.crypto_holding_periods(positions, now=NOW, holding_period_days=365)

    by_ticker = {h.ticker: h for h in out}
    assert by_ticker["BTC"].tax_free is True
    assert by_ticker["BTC"].days_to_tax_free == 0
    assert by_ticker["ETH"].tax_free is False
    assert by_ticker["ETH"].days_held == 100
    assert by_ticker["ETH"].days_to_tax_free == 265
    # On-the-clock lots sort before already-free lots.
    assert out[0].ticker == "ETH"


def test_multiple_lots_per_position_each_tracked():
    out = tax_summary.crypto_holding_periods(
        [_crypto("BTC", _lot(10), _lot(380))], now=NOW, holding_period_days=365
    )
    assert len(out) == 2
    assert {h.tax_free for h in out} == {True, False}
