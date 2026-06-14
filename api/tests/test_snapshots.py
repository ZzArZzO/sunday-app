"""Tests for net-worth snapshots + week-over-week (services/snapshots).

Pure and deterministic — `value_of` runs over in-memory Position objects and
`week_over_week` over lightweight stand-ins, so no DB is needed.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import Position
from app.services import snapshots

NOW = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)


@dataclass
class FakeSnap:
    as_of: datetime
    total_value_eur: Decimal


def _snap(days_ago: float, value: str) -> FakeSnap:
    return FakeSnap(NOW - timedelta(days=days_ago), Decimal(value))


class TestWeekOverWeek:
    def test_unavailable_when_no_old_enough_snapshot(self):
        history = [_snap(2, "10000")]  # only 2 days old
        res = snapshots.week_over_week(history, Decimal("11000"), NOW)
        assert res.available is False
        assert res.delta_eur == Decimal("0") and res.pct == Decimal("0")

    def test_picks_most_recent_snapshot_at_least_a_week_old(self):
        history = [
            _snap(30, "8000"),
            _snap(8, "10000"),   # the baseline (most recent >= 7d old)
            _snap(2, "11500"),   # too recent to be a baseline
        ]
        res = snapshots.week_over_week(history, Decimal("11000"), NOW)
        assert res.available is True
        assert res.baseline_value_eur == Decimal("10000")
        assert res.delta_eur == Decimal("1000.00")
        assert res.pct == Decimal("10.00")
        assert res.baseline_on == (NOW - timedelta(days=8)).date()

    def test_negative_week(self):
        res = snapshots.week_over_week([_snap(7, "20000")], Decimal("19000"), NOW)
        assert res.delta_eur == Decimal("-1000.00")
        assert res.pct == Decimal("-5.00")

    def test_ignores_future_snapshots(self):
        history = [_snap(-3, "99999"), _snap(7, "10000")]  # one dated in the future
        res = snapshots.week_over_week(history, Decimal("10500"), NOW)
        assert res.baseline_value_eur == Decimal("10000")
        assert res.pct == Decimal("5.00")

    def test_zero_baseline_value_yields_zero_pct(self):
        res = snapshots.week_over_week([_snap(7, "0")], Decimal("500"), NOW)
        assert res.available is True
        assert res.delta_eur == Decimal("500.00")
        assert res.pct == Decimal("0")


class TestValueOf:
    def test_totals_and_breakdown_use_live_price(self):
        positions = [
            Position(id=1, ticker="AAPL", asset_class="stock", quantity=Decimal("2"),
                     avg_cost_eur=Decimal("100"), last_price_eur=Decimal("150")),
            Position(id=2, ticker="BTC", asset_class="crypto", quantity=Decimal("0.5"),
                     avg_cost_eur=Decimal("20000"), last_price_eur=Decimal("60000")),
        ]
        total, cost, breakdown = snapshots.value_of(positions)
        assert total == Decimal("30300.00")          # 2*150 + 0.5*60000
        assert cost == Decimal("10200.00")            # 2*100 + 0.5*20000
        assert breakdown["stock"] == Decimal("300.00")
        assert breakdown["crypto"] == Decimal("30000.00")

    def test_missing_price_falls_back_to_cost_basis(self):
        # pnl.market_value_eur uses avg_cost_eur when last_price_eur is None.
        positions = [
            Position(id=3, ticker="X", asset_class="stock", quantity=Decimal("4"),
                     avg_cost_eur=Decimal("25"), last_price_eur=None),
        ]
        total, cost, _ = snapshots.value_of(positions)
        assert total == cost == Decimal("100.00")
