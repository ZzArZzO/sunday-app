"""Concentration analysis.

Thresholds are USER-CONFIGURED (per the legal stance in docs/LEGAL.md). The
defaults here are placeholders for the slice; in production they live on the
user's settings row and the API reads them per-request.
"""

from __future__ import annotations

from decimal import Decimal

from app.models import Position
from app.schemas import ConcentrationItem

# Slice-only placeholder defaults. Real product reads from user settings.
DEFAULT_WARN_PCT = Decimal("5")
DEFAULT_ALERT_PCT = Decimal("10")


def position_weights(
    positions: list[Position], total_value_eur: Decimal
) -> list[tuple[Position, Decimal]]:
    if total_value_eur <= 0:
        return [(p, Decimal("0")) for p in positions]
    from app.services.pnl import market_value_eur

    weights = []
    for p in positions:
        mv = market_value_eur(p)
        pct = (mv / total_value_eur * Decimal("100")).quantize(Decimal("0.01"))
        weights.append((p, pct))
    weights.sort(key=lambda pair: pair[1], reverse=True)
    return weights


def detect_concentration(
    positions: list[Position],
    total_value_eur: Decimal,
    *,
    warn_pct: Decimal = DEFAULT_WARN_PCT,
    alert_pct: Decimal = DEFAULT_ALERT_PCT,
) -> list[ConcentrationItem]:
    items: list[ConcentrationItem] = []
    for pos, pct in position_weights(positions, total_value_eur):
        if pct >= alert_pct:
            severity = "alert"
        elif pct >= warn_pct:
            severity = "warning"
        else:
            continue
        items.append(
            ConcentrationItem(
                ticker=pos.ticker,
                weight_pct=pct,
                threshold_pct=alert_pct if severity == "alert" else warn_pct,
                severity=severity,
            )
        )
    return items


def asset_class_split(
    positions: list[Position], total_value_eur: Decimal
) -> dict[str, Decimal]:
    if total_value_eur <= 0:
        return {}
    from app.services.pnl import market_value_eur

    split: dict[str, Decimal] = {}
    for p in positions:
        mv = market_value_eur(p)
        split[p.asset_class] = split.get(p.asset_class, Decimal("0")) + mv
    return {
        k: (v / total_value_eur * Decimal("100")).quantize(Decimal("0.01"))
        for k, v in split.items()
    }
