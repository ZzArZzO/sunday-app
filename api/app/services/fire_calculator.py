"""FIRE calculator.

Deterministic, formula-based. No optimisation, no Monte Carlo (yet). The math:

    full_fire   = annual_expenses / safe_withdrawal_rate          # the "25x rule" if SWR=4%
    coast_fire  = full_fire / (1 + r) ** (65 - current_age)
    years_full  = ln((full_fire * r + annual_savings) /
                     (current_nw * r + annual_savings)) / ln(1 + r)

All amounts are EUR. The route layer wraps to DualMoney via fx.dual().
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import List

DEFAULT_RETIREMENT_AGE = 65
TIMELINE_MAX_YEARS = 40
LEAN_FIRE_MULTIPLIER = Decimal("0.6")
FAT_FIRE_MULTIPLIER = Decimal("2.0")


@dataclass(frozen=True)
class FireInputs:
    current_net_worth_eur: Decimal
    annual_expenses_eur: Decimal | None
    annual_savings_eur: Decimal | None
    expected_real_return_pct: Decimal
    safe_withdrawal_rate_pct: Decimal
    current_age: int | None = None


@dataclass(frozen=True)
class FireProjectionPoint:
    year_offset: int
    age: int | None
    projected_net_worth_eur: Decimal
    is_coast_fire: bool
    is_full_fire: bool


@dataclass(frozen=True)
class FireCalculation:
    inputs: FireInputs
    full_fire_eur: Decimal
    coast_fire_eur: Decimal
    lean_fire_eur: Decimal
    fat_fire_eur: Decimal
    full_fire_progress_pct: Decimal
    coast_fire_progress_pct: Decimal
    years_to_full_fire: Decimal | None
    years_to_coast_fire: Decimal | None
    timeline: List[FireProjectionPoint]
    notes: list[str]


def _to_rate(pct: Decimal) -> Decimal:
    return pct / Decimal("100")


def _full_fire_number(annual_expenses: Decimal, swr_pct: Decimal) -> Decimal:
    rate = _to_rate(swr_pct)
    if rate <= 0:
        return Decimal("0")
    return (annual_expenses / rate).quantize(Decimal("0.01"))


def _coast_fire_number(
    full_fire: Decimal, real_return_pct: Decimal, years_until_retirement: int
) -> Decimal:
    if years_until_retirement <= 0:
        return full_fire
    r = _to_rate(real_return_pct)
    growth = (Decimal("1") + r) ** years_until_retirement
    if growth <= 0:
        return full_fire
    return (full_fire / growth).quantize(Decimal("0.01"))


def _years_to_target(
    target_eur: Decimal,
    current_nw_eur: Decimal,
    annual_savings_eur: Decimal,
    real_return_pct: Decimal,
) -> Decimal | None:
    """Solve for n in: target = current * (1+r)^n + savings * (((1+r)^n - 1)/r)

    Returns None when the target is unreachable (no return, no savings, etc.).
    """
    if current_nw_eur >= target_eur:
        return Decimal("0")

    r = float(_to_rate(real_return_pct))
    target = float(target_eur)
    current = float(current_nw_eur)
    savings = float(annual_savings_eur)

    if r <= 0 and savings <= 0:
        return None
    if r == 0:
        # Pure savings, no growth
        if savings <= 0:
            return None
        return Decimal(str((target - current) / savings)).quantize(Decimal("0.1"))

    # Solve (current + savings/r) * (1+r)^n - savings/r = target
    numerator = target * r + savings
    denominator = current * r + savings
    if denominator <= 0 or numerator <= 0:
        return None
    try:
        years = math.log(numerator / denominator) / math.log(1 + r)
    except (ValueError, ZeroDivisionError):
        return None
    if years < 0 or years > 1000:
        return None
    return Decimal(str(years)).quantize(Decimal("0.1"))


def _build_timeline(
    inputs: FireInputs,
    full_fire_eur: Decimal,
    coast_fire_eur: Decimal,
) -> list[FireProjectionPoint]:
    r = _to_rate(inputs.expected_real_return_pct)
    savings = inputs.annual_savings_eur or Decimal("0")
    nw = inputs.current_net_worth_eur

    points: list[FireProjectionPoint] = []
    for offset in range(0, TIMELINE_MAX_YEARS + 1):
        age = inputs.current_age + offset if inputs.current_age is not None else None
        points.append(
            FireProjectionPoint(
                year_offset=offset,
                age=age,
                projected_net_worth_eur=nw.quantize(Decimal("0.01")),
                is_coast_fire=nw >= coast_fire_eur > 0,
                is_full_fire=nw >= full_fire_eur > 0,
            )
        )
        nw = nw * (Decimal("1") + r) + savings
    return points


def calculate(inputs: FireInputs) -> FireCalculation:
    notes: list[str] = []

    if inputs.annual_expenses_eur is None or inputs.annual_expenses_eur <= 0:
        notes.append(
            "Set your annual expenses to see full FIRE numbers. "
            "Defaults to €30,000/year for the preview."
        )
        annual_expenses = Decimal("30000")
    else:
        annual_expenses = inputs.annual_expenses_eur

    if inputs.annual_savings_eur is None or inputs.annual_savings_eur <= 0:
        notes.append(
            "Set your annual savings to see a years-to-FIRE projection. "
            "Defaults to €12,000/year for the preview."
        )
        annual_savings = Decimal("12000")
    else:
        annual_savings = inputs.annual_savings_eur

    full_fire = _full_fire_number(annual_expenses, inputs.safe_withdrawal_rate_pct)
    years_until_retirement = (
        DEFAULT_RETIREMENT_AGE - inputs.current_age
        if inputs.current_age is not None
        else 30
    )
    coast_fire = _coast_fire_number(
        full_fire, inputs.expected_real_return_pct, max(years_until_retirement, 0)
    )
    lean_fire = (full_fire * LEAN_FIRE_MULTIPLIER).quantize(Decimal("0.01"))
    fat_fire = (full_fire * FAT_FIRE_MULTIPLIER).quantize(Decimal("0.01"))

    full_progress = (
        (inputs.current_net_worth_eur / full_fire * Decimal("100")).quantize(Decimal("0.01"))
        if full_fire > 0
        else Decimal("0")
    )
    coast_progress = (
        (inputs.current_net_worth_eur / coast_fire * Decimal("100")).quantize(Decimal("0.01"))
        if coast_fire > 0
        else Decimal("0")
    )

    # Re-derive an "effective" inputs object for the math helpers that uses the
    # backfilled defaults rather than None, so the timeline is always drawable.
    effective_inputs = FireInputs(
        current_net_worth_eur=inputs.current_net_worth_eur,
        annual_expenses_eur=annual_expenses,
        annual_savings_eur=annual_savings,
        expected_real_return_pct=inputs.expected_real_return_pct,
        safe_withdrawal_rate_pct=inputs.safe_withdrawal_rate_pct,
        current_age=inputs.current_age,
    )

    years_full = _years_to_target(
        full_fire,
        inputs.current_net_worth_eur,
        annual_savings,
        inputs.expected_real_return_pct,
    )
    years_coast = _years_to_target(
        coast_fire,
        inputs.current_net_worth_eur,
        annual_savings,
        inputs.expected_real_return_pct,
    )
    timeline = _build_timeline(effective_inputs, full_fire, coast_fire)

    return FireCalculation(
        inputs=effective_inputs,
        full_fire_eur=full_fire,
        coast_fire_eur=coast_fire,
        lean_fire_eur=lean_fire,
        fat_fire_eur=fat_fire,
        full_fire_progress_pct=full_progress,
        coast_fire_progress_pct=coast_progress,
        years_to_full_fire=years_full,
        years_to_coast_fire=years_coast,
        timeline=timeline,
        notes=notes,
    )
