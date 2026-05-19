"""P&L and valuation helpers.

For the MVP slice we use the position's `last_price_eur` if set, otherwise we
fall back to `avg_cost_eur` (so P&L shows zero rather than crashing). Phase 2
will populate `last_price_eur` from the price fetcher on a schedule.
"""

from __future__ import annotations

from decimal import Decimal

from app.models import Position


def market_value_eur(position: Position) -> Decimal:
    price = position.last_price_eur if position.last_price_eur is not None else position.avg_cost_eur
    return (position.quantity * price).quantize(Decimal("0.01"))


def cost_basis_eur(position: Position) -> Decimal:
    return (position.quantity * position.avg_cost_eur).quantize(Decimal("0.01"))


def unrealised_pnl_eur(position: Position) -> Decimal:
    return (market_value_eur(position) - cost_basis_eur(position)).quantize(Decimal("0.01"))
