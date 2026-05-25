"""Dividend income projector.

We don't have live dividend data yet, so we estimate annual yield from
per-asset-class defaults and an overlay of ticker-level overrides for the
commonly-held European ETFs and dividend stocks. Phase 2 will swap the
overlay for a real fetcher.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models import Position

# Annual yield estimates by asset class (informational).
ASSET_CLASS_YIELD_PCT: dict[str, Decimal] = {
    "etf": Decimal("1.80"),  # accumulating ETFs distribute internally — show indicative gross
    "stock": Decimal("2.50"),
    "crypto": Decimal("0.00"),
    "cash": Decimal("3.00"),  # money-market estimate
}

# Per-ticker overrides for the most common European holdings. These are
# representative figures; the real fetcher will replace them.
TICKER_YIELD_OVERRIDES_PCT: dict[str, Decimal] = {
    # Dividend-distributing ETFs
    "VHYL": Decimal("3.50"),
    "VHYD": Decimal("3.50"),
    "EUNL": Decimal("1.80"),
    "VWRL": Decimal("1.90"),
    # Accumulating ETFs (gross-of-tax indicative yield)
    "VWCE": Decimal("1.80"),
    "SXR8": Decimal("1.30"),
    # Dividend-paying European stocks
    "NESN": Decimal("3.20"),
    "SAN": Decimal("4.00"),
    "ASML": Decimal("0.80"),
    "ALV": Decimal("4.50"),
    "BAS": Decimal("5.80"),
    "SHEL": Decimal("4.00"),
    "BATS": Decimal("8.20"),
}

# Average annual dividend growth assumption for the EU large-cap basket.
DEFAULT_DIVIDEND_GROWTH_PCT = Decimal("5.00")


@dataclass(frozen=True)
class DividendLine:
    position: Position
    market_value_eur: Decimal
    yield_pct: Decimal
    annual_dividend_eur: Decimal
    source: str


def _yield_for(position: Position) -> tuple[Decimal, str]:
    override = TICKER_YIELD_OVERRIDES_PCT.get(position.ticker.upper())
    if override is not None:
        return override, "known"
    return ASSET_CLASS_YIELD_PCT.get(position.asset_class, Decimal("0")), "estimate"


def project(positions: list[Position], market_values_eur: dict[int, Decimal]) -> list[DividendLine]:
    """Build per-position dividend projection lines.

    `market_values_eur` is passed in to avoid recomputing pnl.market_value_eur()
    when the caller already has it.
    """
    lines: list[DividendLine] = []
    for pos in positions:
        mv = market_values_eur.get(pos.id, Decimal("0"))
        yield_pct, source = _yield_for(pos)
        annual = (mv * yield_pct / Decimal("100")).quantize(Decimal("0.01"))
        lines.append(
            DividendLine(
                position=pos,
                market_value_eur=mv,
                yield_pct=yield_pct,
                annual_dividend_eur=annual,
                source=source,
            )
        )
    return lines


def total_annual_eur(lines: list[DividendLine]) -> Decimal:
    return sum((line.annual_dividend_eur for line in lines), start=Decimal("0")).quantize(
        Decimal("0.01")
    )


def weighted_yield_pct(lines: list[DividendLine]) -> Decimal:
    total_value = sum((line.market_value_eur for line in lines), start=Decimal("0"))
    if total_value <= 0:
        return Decimal("0")
    return (total_annual_eur(lines) / total_value * Decimal("100")).quantize(Decimal("0.01"))
