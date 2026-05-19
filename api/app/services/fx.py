"""FX conversion service.

For the MVP slice this returns a hardcoded EUR/USD rate. Phase 2 will fetch live
rates from yfinance (`EURUSD=X`) with a 1-hour in-memory cache and a daily
persisted snapshot for backdated P&L.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


# Placeholder rate. Replace with live fetch in Phase 2.
_PLACEHOLDER_EUR_USD = Decimal("1.0800")


@dataclass(frozen=True)
class FxQuote:
    pair: str
    rate: Decimal
    fetched_at: datetime
    source: str


def get_eur_usd() -> FxQuote:
    return FxQuote(
        pair="EUR/USD",
        rate=_PLACEHOLDER_EUR_USD,
        fetched_at=datetime.now(timezone.utc),
        source="placeholder",
    )


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
