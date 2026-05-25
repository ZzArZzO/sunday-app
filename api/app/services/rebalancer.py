"""Asset-class rebalancing suggestions.

Compares current vs target allocation by asset class and outputs delta amounts
(positive = buy more, negative = sell some). Threshold-band style: if no leg
drifts more than `DRIFT_TRIGGER_PCT` from target, the leg's action is `hold`.

This is intentionally conservative — no per-ticker suggestions yet, because that
needs richer holdings metadata (sectors, factor exposures) we haven't captured.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models import Position, User

DRIFT_TRIGGER_PCT = Decimal("5.00")
ASSET_CLASSES = ("etf", "stock", "crypto", "cash")


@dataclass(frozen=True)
class RebalanceLegCalc:
    asset_class: str
    current_pct: Decimal
    target_pct: Decimal
    current_value_eur: Decimal
    target_value_eur: Decimal
    delta_eur: Decimal
    action: str


@dataclass(frozen=True)
class RebalanceCalc:
    total_value_eur: Decimal
    drift_score: Decimal
    needs_rebalance: bool
    legs: list[RebalanceLegCalc]
    notes: list[str]


def _target_pct_map(user: User) -> dict[str, Decimal]:
    return {
        "etf": user.target_etf_pct,
        "stock": user.target_stock_pct,
        "crypto": user.target_crypto_pct,
        "cash": user.target_cash_pct,
    }


def _current_value_by_class(positions: list[Position]) -> dict[str, Decimal]:
    from app.services.pnl import market_value_eur

    out: dict[str, Decimal] = {cls: Decimal("0") for cls in ASSET_CLASSES}
    for p in positions:
        out.setdefault(p.asset_class, Decimal("0"))
        out[p.asset_class] += market_value_eur(p)
    return out


def suggest(positions: list[Position], user: User) -> RebalanceCalc:
    targets = _target_pct_map(user)
    target_total = sum(targets.values(), start=Decimal("0"))
    notes: list[str] = []
    if target_total <= 0:
        notes.append("No target allocation set — using current allocation as the target.")
    elif abs(target_total - Decimal("100")) > Decimal("0.01"):
        notes.append(
            f"Target allocation sums to {target_total:.2f}% — should be 100%. "
            "Normalising for this calculation."
        )

    current = _current_value_by_class(positions)
    total_value = sum(current.values(), start=Decimal("0"))
    if total_value <= 0:
        return RebalanceCalc(
            total_value_eur=Decimal("0"),
            drift_score=Decimal("0"),
            needs_rebalance=False,
            legs=[],
            notes=["No positions to rebalance — upload a portfolio first."],
        )

    legs: list[RebalanceLegCalc] = []
    drift_total = Decimal("0")
    for cls in ASSET_CLASSES:
        cv = current.get(cls, Decimal("0"))
        cpct = (cv / total_value * Decimal("100")).quantize(Decimal("0.01"))
        # Normalise targets if they don't sum to 100
        raw_target = targets.get(cls, Decimal("0"))
        tpct = (
            (raw_target / target_total * Decimal("100")).quantize(Decimal("0.01"))
            if target_total > 0
            else cpct
        )
        target_value = (total_value * tpct / Decimal("100")).quantize(Decimal("0.01"))
        delta = (target_value - cv).quantize(Decimal("0.01"))
        drift = (cpct - tpct).quantize(Decimal("0.01"))
        drift_total += abs(drift)

        if abs(drift) < DRIFT_TRIGGER_PCT:
            action = "hold"
        elif delta > 0:
            action = "buy"
        else:
            action = "sell"

        legs.append(
            RebalanceLegCalc(
                asset_class=cls,
                current_pct=cpct,
                target_pct=tpct,
                current_value_eur=cv.quantize(Decimal("0.01")),
                target_value_eur=target_value,
                delta_eur=delta,
                action=action,
            )
        )

    needs = any(leg.action != "hold" for leg in legs)
    return RebalanceCalc(
        total_value_eur=total_value.quantize(Decimal("0.01")),
        drift_score=drift_total.quantize(Decimal("0.01")),
        needs_rebalance=needs,
        legs=legs,
        notes=notes,
    )
