"""Price refresh orchestration.

`price_positions` is the pure core: given positions + a provider + FX rates, it
fetches each holding's price, converts to EUR, writes `last_price_eur` /
`last_price_at`, and returns a result with counts + warnings. It mutates the
position objects but does NOT touch the database or the network directly — the
route commits, the provider does I/O — so it unit-tests with a fake provider.

Symbol resolution:
    crypto  → try `{ticker}-EUR`, then `{ticker}-USD`
    other   → the stored ticker as-is (best effort; unresolved → warning)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.models import Position
from app.services import fx
from app.services.prices import symbols
from app.services.prices.base import PriceProvider, Quote
from app.services.prices.convert import to_eur

# last_price_eur is Numeric(18, 4) — quantise to match the column scale.
_PRICE_Q = Decimal("0.0001")

# Non-USD currencies we fetch a EUR cross rate for (yfinance pair, currency code).
_CROSS_PAIRS = (("GBPEUR=X", "GBP"), ("CHFEUR=X", "CHF"))


@dataclass
class RefreshResult:
    priced: int = 0
    unpriced: int = 0
    total: int = 0
    warnings: list[str] = field(default_factory=list)


def _quote_for(
    provider: PriceProvider, position: Position, isin_map: dict[str, str] | None = None
) -> Quote | None:
    for symbol in symbols.candidate_symbols(position, isin_map=isin_map):
        quote = provider.get_quote(symbol)
        if quote is not None:
            return quote
    return None


def price_positions(
    positions: list[Position],
    provider: PriceProvider,
    *,
    eur_usd_rate: Decimal,
    cross_rates: dict[str, Decimal] | None = None,
    isin_map: dict[str, str] | None = None,
    now: datetime,
) -> RefreshResult:
    result = RefreshResult(total=len(positions))

    for p in positions:
        quote = _quote_for(provider, p, isin_map)
        if quote is None:
            result.unpriced += 1
            if not p.ticker:
                result.warnings.append(f"UNPRICED: position {p.id} has no ticker")
            else:
                result.warnings.append(f"PRICE_FETCH_FAILED: {p.ticker} ({p.asset_class})")
            continue

        converted = to_eur(
            quote.price,
            quote.currency,
            eur_usd_rate=eur_usd_rate,
            cross_rates=cross_rates,
        )
        if converted.eur is None:
            result.unpriced += 1
            result.warnings.append(f"PRICE_CONVERT_FAILED: {p.ticker}: {converted.note}")
            continue

        p.last_price_eur = converted.eur.quantize(_PRICE_Q)
        p.last_price_at = now
        result.priced += 1

    return result


def refresh_eur_usd(provider: PriceProvider) -> Decimal | None:
    """Fetch live EUR/USD (USD per 1 EUR) and update the FX cache. None on failure."""
    quote = provider.get_quote("EURUSD=X")
    if quote is None or quote.price <= 0:
        return None
    fx.set_eur_usd(quote.price, source="yfinance")
    return quote.price


def safe_rate(provider: PriceProvider, symbol: str) -> Decimal | None:
    """Best-effort cross rate (e.g. GBPEUR=X). None if unavailable — never raises."""
    quote = provider.get_quote(symbol)
    if quote is None or quote.price <= 0:
        return None
    return quote.price


def fetch_cross_rates(provider: PriceProvider) -> dict[str, Decimal]:
    """Best-effort {CURRENCY: EUR-per-1-unit} map for non-USD listings (GBP, CHF…)."""
    rates: dict[str, Decimal] = {}
    for pair, code in _CROSS_PAIRS:
        rate = safe_rate(provider, pair)
        if rate is not None:
            rates[code] = rate
    return rates
