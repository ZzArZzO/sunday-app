"""Tests for benchmark comparison (services/benchmark).

Pure: TWR runs over duck-typed snapshots; index alignment uses a fake history.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.services import benchmark


def _snap(d: str, value: str, cost: str):
    return SimpleNamespace(
        captured_on=date.fromisoformat(d),
        total_value_eur=Decimal(value),
        total_cost_eur=Decimal(cost),
    )


class _FakeHistory:
    def __init__(self, closes: dict[date, Decimal]):
        self._closes = closes

    def get_closes(self, symbol, start, end):
        return self._closes


class TestTwrSeries:
    def test_needs_two_snapshots(self):
        assert benchmark.twr_series([_snap("2026-06-01", "1000", "1000")]) == []

    def test_pure_market_move_no_flows(self):
        # +10% with no new money → cumulative TWR 10%.
        snaps = [_snap("2026-06-01", "1000", "1000"), _snap("2026-06-08", "1100", "1000")]
        pts = benchmark.twr_series(snaps)
        assert pts[0].twr_pct == Decimal("0")
        assert pts[-1].twr_pct == Decimal("10.00")

    def test_deposit_is_excluded_from_return(self):
        # Value 1000 → 2000 but +1000 was deposited (cost 1000 → 2000): 0% return.
        snaps = [_snap("2026-06-01", "1000", "1000"), _snap("2026-06-08", "2000", "2000")]
        pts = benchmark.twr_series(snaps)
        assert pts[-1].twr_pct == Decimal("0.00")


class TestBuildComparison:
    def test_unavailable_without_history(self):
        cmp = benchmark.build_comparison(
            [_snap("2026-06-01", "1000", "1000")], "msci_world", _FakeHistory({})
        )
        assert cmp.available is False
        assert cmp.note is not None

    def test_compares_against_index(self):
        snaps = [_snap("2026-06-01", "1000", "1000"), _snap("2026-06-08", "1100", "1000")]
        closes = {date(2026, 6, 1): Decimal("100"), date(2026, 6, 8): Decimal("105")}
        cmp = benchmark.build_comparison(snaps, "msci_world", _FakeHistory(closes))
        assert cmp.available is True
        assert cmp.index_available is True
        assert cmp.portfolio_pct == Decimal("10.00")
        assert cmp.index_pct == Decimal("5.00")
        assert cmp.diff_pct == Decimal("5.00")
        # +5% of the latest €1,100 value.
        assert cmp.diff_eur == Decimal("55.00")

    def test_index_unavailable_still_returns_portfolio(self):
        snaps = [_snap("2026-06-01", "1000", "1000"), _snap("2026-06-08", "1100", "1000")]
        cmp = benchmark.build_comparison(snaps, "sp500", _FakeHistory({}))
        assert cmp.available is True
        assert cmp.index_available is False
        assert cmp.portfolio_pct == Decimal("10.00")
        assert cmp.diff_pct is None
