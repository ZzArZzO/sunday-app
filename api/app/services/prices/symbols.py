"""Resolve a holding to the market symbols a price provider understands.

TR-style tickers ("VWCE", "SXR8", "NESN") don't resolve on Yahoo as-is — EU
listings need an exchange suffix (VWCE.DE, NESN.SW). This mirrors the seed's
ISIN→ticker map (`investment-ai/data/isin-ticker-map.json`), but resolution is
ordered so the right venue wins:

    1. Curated ISIN → symbol map (most reliable; verified against the provider).
    2. Bare ticker (works for US listings like AAPL).
    3. Exchange-suffix fallbacks for the long tail (EUR venues first).

`candidate_symbols` returns an ordered, de-duplicated list; the provider tries
each until one quotes. Crypto stays special: `{TICKER}-EUR` then `{TICKER}-USD`.
"""

from __future__ import annotations

# ISIN → yfinance symbol. Verified live; extend as holdings appear.
ISIN_TICKER_MAP: dict[str, str] = {
    "IE00BK5BQT80": "VWCE.DE",   # Vanguard FTSE All-World UCITS Acc (Xetra, EUR)
    "IE00B5BMR087": "SXR8.DE",   # iShares Core S&P 500 UCITS Acc (Xetra, EUR)
    "NL0010273215": "ASML.AS",   # ASML Holding (Amsterdam, EUR — the home listing)
    "CH0038863350": "NESN.SW",   # Nestlé (SIX Swiss, CHF)
}

# Bare-ticker overrides for holdings that have no ISIN on file.
TICKER_OVERRIDES: dict[str, str] = {}

# Suffixes to try when a bare EU ticker doesn't resolve. EUR venues first so a
# EUR-priced holding isn't accidentally matched to a foreign-currency listing.
_EUR_SUFFIXES = (".DE", ".AS", ".PA", ".MI", ".VI")  # Xetra, Amsterdam, Paris, Milan, Vienna
_OTHER_SUFFIXES = (".SW", ".L")  # Swiss (CHF), London (GBp/GBP)


def _dedup(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in symbols:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def candidate_symbols(position, isin_map: dict[str, str] | None = None) -> list[str]:
    """Ordered yfinance symbols to try for this position.

    `isin_map` is an optional resolved ISIN→symbol map (DB cache / OpenFIGI) that
    fills the long tail beyond the curated `ISIN_TICKER_MAP`. The curated map takes
    precedence where both have an entry (it's hand-verified).
    """
    if position.asset_class == "crypto":
        ticker = (position.ticker or "").strip().upper()
        return [f"{ticker}-EUR", f"{ticker}-USD"] if ticker else []

    candidates: list[str] = []

    isin = (position.isin or "").strip().upper()
    merged_isin_map = {**(isin_map or {}), **ISIN_TICKER_MAP}
    if isin and isin in merged_isin_map:
        candidates.append(merged_isin_map[isin])

    ticker = (position.ticker or "").strip().upper()
    if ticker in TICKER_OVERRIDES:
        candidates.append(TICKER_OVERRIDES[ticker])

    if ticker:
        candidates.append(ticker)  # bare — resolves for US listings
        # Only guess suffixes for plain symbols (not already-suffixed or pairs).
        if "." not in ticker and "-" not in ticker:
            for suffix in _EUR_SUFFIXES + _OTHER_SUFFIXES:
                candidates.append(f"{ticker}{suffix}")

    return _dedup(candidates)
