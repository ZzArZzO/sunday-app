"""Portfolio snapshots + week-over-week.

`value_of` and `week_over_week` are pure (testable without a DB); `capture`
upserts one row per portfolio per day. The briefing compares the live value to
the most recent snapshot ~7 days old — which is what finally replaces the
hardcoded `wow_delta = 0`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Portfolio, PortfolioSnapshot
from app.services import fx, pnl

DEFAULT_LOOKBACK_DAYS = 7


def value_of(positions: list) -> tuple[Decimal, Decimal, dict[str, Decimal]]:
    """Return (total_value_eur, total_cost_eur, per-asset-class value) for positions."""
    total = sum((pnl.market_value_eur(p) for p in positions), start=Decimal("0"))
    cost = sum((pnl.cost_basis_eur(p) for p in positions), start=Decimal("0"))
    breakdown: dict[str, Decimal] = {}
    for p in positions:
        breakdown[p.asset_class] = breakdown.get(p.asset_class, Decimal("0")) + pnl.market_value_eur(p)
    return total, cost, breakdown


def current_value(portfolio: Portfolio) -> tuple[Decimal, Decimal, dict[str, Decimal]]:
    return value_of(list(portfolio.positions))


class _HasSnapshotFields(Protocol):
    as_of: datetime
    total_value_eur: Decimal


@dataclass(frozen=True)
class WowResult:
    available: bool
    delta_eur: Decimal
    pct: Decimal
    baseline_on: date | None
    baseline_value_eur: Decimal | None


def week_over_week(
    history: list[_HasSnapshotFields],
    current_value_eur: Decimal,
    now: datetime,
    *,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> WowResult:
    """Compare the current value to the most recent snapshot at least `lookback_days` old.

    Returns `available=False` (no fake 0) until such a baseline exists.
    """
    target = now - timedelta(days=lookback_days)
    eligible = [s for s in history if s.as_of <= target]
    if not eligible:
        return WowResult(False, Decimal("0"), Decimal("0"), None, None)

    baseline = max(eligible, key=lambda s: s.as_of)
    base_val = baseline.total_value_eur
    delta = (current_value_eur - base_val).quantize(Decimal("0.01"))
    pct = (
        (delta / base_val * Decimal("100")).quantize(Decimal("0.01"))
        if base_val > 0
        else Decimal("0")
    )
    baseline_on = baseline.as_of.date() if hasattr(baseline.as_of, "date") else None
    return WowResult(True, delta, pct, baseline_on, base_val)


def capture(db: Session, portfolio: Portfolio, *, now: datetime) -> PortfolioSnapshot:
    """Record (or update) today's net-worth snapshot for this portfolio."""
    total, cost, breakdown = current_value(portfolio)
    rate = fx.get_eur_usd().rate
    day = now.date()
    breakdown_json = {cls: str(amount.quantize(Decimal("0.01"))) for cls, amount in breakdown.items()}

    existing = db.execute(
        select(PortfolioSnapshot).where(
            PortfolioSnapshot.portfolio_id == portfolio.id,
            PortfolioSnapshot.captured_on == day,
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.as_of = now
        existing.total_value_eur = total.quantize(Decimal("0.01"))
        existing.total_cost_eur = cost.quantize(Decimal("0.01"))
        existing.eur_usd_rate = rate
        existing.breakdown = breakdown_json
        db.flush()
        return existing

    snap = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        captured_on=day,
        as_of=now,
        total_value_eur=total.quantize(Decimal("0.01")),
        total_cost_eur=cost.quantize(Decimal("0.01")),
        eur_usd_rate=rate,
        breakdown=breakdown_json,
    )
    db.add(snap)
    db.flush()
    return snap
