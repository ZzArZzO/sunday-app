"""FX conversion service.

Holds the latest EUR/USD rate in a process-local cache. `services/prices`
refreshes it from yfinance (`EURUSD=X`); until the first refresh — or after a
restart — `get_eur_usd()` falls back to a clearly-labelled placeholder so reads
never fail. (Persisting the rate across restarts is a follow-up.)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


# Fallback used only until the first live refresh populates the cache.
_PLACEHOLDER_EUR_USD = Decimal("1.0800")

# Process-local cache of the most recently refreshed rate.
_cache: "FxQuote | None" = None


@dataclass(frozen=True)
class FxQuote:
    pair: str
    rate: Decimal
    fetched_at: datetime
    source: str


def get_eur_usd() -> FxQuote:
    if _cache is not None:
        return _cache
    return FxQuote(
        pair="EUR/USD",
        rate=_PLACEHOLDER_EUR_USD,
        fetched_at=datetime.now(timezone.utc),
        source="placeholder",
    )


def set_eur_usd(rate: Decimal, source: str = "yfinance") -> FxQuote:
    """Update the cached EUR/USD rate (USD per 1 EUR)."""
    global _cache
    _cache = FxQuote(
        pair="EUR/USD",
        rate=rate,
        fetched_at=datetime.now(timezone.utc),
        source=source,
    )
    return _cache


def usd_to_eur(amount_usd: Decimal, rate: Decimal | None = None) -> Decimal:
    if rate is None:
        rate = get_eur_usd().rate
    return (amount_usd / rate).quantize(Decimal("0.01"))


def eur_to_usd(amount_eur: Decimal, rate: Decimal | None = None) -> Decimal:
    if rate is None:
        rate = get_eur_usd().rate
    return (amount_eur * rate).quantize(Decimal("0.01"))


def dual(amount_eur: Decimal, rate: Decimal | None = None) -> dict[str, Decimal]:
    if rate is None:
        rate = get_eur_usd().rate
    return {
        "eur": amount_eur.quantize(Decimal("0.01")),
        "usd": eur_to_usd(amount_eur, rate),
    }
