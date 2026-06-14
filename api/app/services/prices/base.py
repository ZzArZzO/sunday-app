"""Price provider boundary: the one place market-data I/O is abstracted.

`price_positions` (refresh.py) depends only on `PriceProvider`, so it can be
driven by the real yfinance provider in production and a fake in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class PricesUnavailable(RuntimeError):
    """Raised when the price backend (yfinance/curl_cffi) can't be loaded."""


@dataclass(frozen=True)
class Quote:
    """A single market quote in its native currency."""

    symbol: str
    price: Decimal
    currency: str
    source: str


class PriceProvider(Protocol):
    def get_quote(self, symbol: str) -> Quote | None:
        """Return the latest quote for a market symbol, or None if unavailable."""
        ...
