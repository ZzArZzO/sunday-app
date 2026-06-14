"""Real price provider, backed by yfinance.

Yahoo's WAF rate-limits Python's default TLS fingerprint hard (sticky 429s), so
we route yfinance through a curl_cffi Chrome-impersonation session — the exact
trick proven in the seed (`investment-ai/scripts/finance_mcp_runner.py`).

yfinance and curl_cffi are imported lazily so the rest of the app (and the unit
tests, which inject a fake provider) don't depend on them being installed.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from app.services.prices.base import PriceProvider, PricesUnavailable, Quote

log = logging.getLogger(__name__)

# Shared, lazily-initialised patched yfinance module — reused by the price
# provider and the events/news layer so the curl_cffi session + Ticker patch is
# set up exactly once.
_YF = None


def get_yf():
    """Return yfinance with a Chrome-impersonating session injected (anti-429)."""
    global _YF
    if _YF is not None:
        return _YF
    try:
        from curl_cffi import requests as curl_requests
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise PricesUnavailable(
            "Market data requires 'yfinance' and 'curl_cffi'. "
            "Install them: pip install yfinance curl_cffi"
        ) from exc

    session = curl_requests.Session(impersonate="chrome")
    original_init = yf.Ticker.__init__

    def _patched_init(ticker_self, ticker, session_kw=None, *args, **kwargs):
        if session_kw is None:
            session_kw = session
        original_init(ticker_self, ticker, session=session_kw, *args, **kwargs)

    if not getattr(yf.Ticker.__init__, "_sunday_patched", False):
        _patched_init._sunday_patched = True  # type: ignore[attr-defined]
        yf.Ticker.__init__ = _patched_init  # type: ignore[method-assign]

    _YF = yf
    return yf


class YFinanceProvider(PriceProvider):
    def __init__(self) -> None:
        self._yf = None  # lazily initialised

    def _ensure_yf(self):
        if self._yf is not None:
            return self._yf
        try:
            from curl_cffi import requests as curl_requests
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise PricesUnavailable(
                "Price data requires 'yfinance' and 'curl_cffi'. "
                "Install them: pip install yfinance curl_cffi"
            ) from exc

        # Inject a Chrome-impersonating session into every Ticker (seed pattern).
        session = curl_requests.Session(impersonate="chrome")
        original_init = yf.Ticker.__init__

        def _patched_init(ticker_self, ticker, session_kw=None, *args, **kwargs):
            if session_kw is None:
                session_kw = session
            original_init(ticker_self, ticker, session=session_kw, *args, **kwargs)

        if not getattr(yf.Ticker.__init__, "_sunday_patched", False):
            _patched_init._sunday_patched = True  # type: ignore[attr-defined]
            yf.Ticker.__init__ = _patched_init  # type: ignore[method-assign]

        self._yf = yf
        return yf

    def get_quote(self, symbol: str) -> Quote | None:
        if not symbol:
            return None
        yf = self._ensure_yf()

        # Primary: fast_info (cheap, single request).
        try:
            t = yf.Ticker(symbol)
            fi = t.fast_info
            price = fi.get("lastPrice") if hasattr(fi, "get") else fi.last_price
            currency = fi.get("currency") if hasattr(fi, "get") else fi.currency
            if price is not None and price == price and float(price) > 0:  # not NaN
                return Quote(symbol, Decimal(str(price)), currency or "USD", "yfinance.fast_info")
        except Exception as exc:  # noqa: BLE001 - yfinance raises many types
            log.warning("fast_info failed for %s: %s", symbol, exc)

        # Fallback: last close from 2-day history.
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="2d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                try:
                    currency = t.info.get("currency")
                except Exception:  # noqa: BLE001
                    currency = None
                if price > 0:
                    return Quote(symbol, Decimal(str(price)), currency or "USD", "yfinance.history")
        except Exception as exc:  # noqa: BLE001
            log.warning("history fallback failed for %s: %s", symbol, exc)

        return None

    def get_closes(self, symbol: str, start: date, end: date) -> dict[date, Decimal]:
        """Daily closing prices in [start, end] for benchmark series. {} on failure."""
        if not symbol:
            return {}
        yf = self._ensure_yf()
        try:
            t = yf.Ticker(symbol)
            # yfinance `end` is exclusive — add a day to include the end date.
            hist = t.history(start=start.isoformat(), end=(end + timedelta(days=1)).isoformat())
            if hist.empty:
                return {}
            out: dict[date, Decimal] = {}
            for idx, close in hist["Close"].items():
                day = idx.date() if hasattr(idx, "date") else idx
                out[day] = Decimal(str(float(close)))
            return out
        except Exception as exc:  # noqa: BLE001
            log.warning("get_closes failed for %s: %s", symbol, exc)
            return {}
