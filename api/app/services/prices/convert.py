"""Pure native-currency → EUR conversion.

Ported from the seed's `to_eur_and_usd` (investment-ai/scripts/build_snapshot.py).
Sunday's base currency is EUR, so we only need the EUR leg here.

USD converts via `eur_usd_rate` (USD per 1 EUR). Every other non-EUR currency
converts via `cross_rates` — a {CURRENCY: EUR-per-1-unit} map the caller fetches
(e.g. {"GBP": 1.16, "CHF": 1.08}). London pence (GBp/GBX) divides by 100 then
uses the GBP rate. Unknown currencies return a note so the caller can warn
rather than silently mis-value a holding.

IMPORTANT: check pence ('GBp'/'GBX') BEFORE uppercasing — uppercasing 'GBp' to
'GBP' collapses the distinction and would value a London holding 100x too high.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

_HUNDRED = Decimal("100")
_PENCE = {"GBp", "GBX"}


@dataclass(frozen=True)
class ConversionResult:
    eur: Decimal | None
    note: str | None  # populated only when eur is None


def to_eur(
    price: Decimal,
    currency: str | None,
    *,
    eur_usd_rate: Decimal,
    cross_rates: dict[str, Decimal] | None = None,
) -> ConversionResult:
    """Convert a native price + currency to EUR. `eur_usd_rate` is USD per 1 EUR."""
    if eur_usd_rate <= 0:
        return ConversionResult(None, "invalid EUR/USD rate")

    rates = cross_rates or {}
    raw = currency or ""

    # Pence — must be handled before the .upper() below.
    if raw in _PENCE:
        gbp = rates.get("GBP")
        if gbp is None:
            return ConversionResult(None, f"no GBP/EUR rate for {raw!r}")
        return ConversionResult(price / _HUNDRED * gbp, None)

    cur = raw.upper()
    if cur in ("", "EUR"):
        return ConversionResult(price, None)
    if cur == "USD":
        return ConversionResult(price / eur_usd_rate, None)

    rate = rates.get(cur)
    if rate is not None:
        return ConversionResult(price * rate, None)

    return ConversionResult(None, f"unsupported currency {currency!r}")
