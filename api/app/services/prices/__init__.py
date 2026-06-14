"""Live price + FX layer.

Replaces the MVP placeholders (P&L that fell back to cost basis, a hardcoded
EUR/USD of 1.08) with real market values, so every downstream number — P&L,
week-over-week, the briefing, the assistant's grounding — is true.

Ported from the seed project (`investment-ai/scripts/build_snapshot.py`): the
same yfinance + curl_cffi pattern and currency conversion, re-shaped into a
testable service.

Design:
    base.py             — Quote + PriceProvider protocol (I/O boundary)
    convert.py          — pure native-currency → EUR conversion
    yfinance_provider.py — the real provider (yfinance, lazily imported)
    refresh.py          — price_positions() (pure core) + EUR/USD refresh

The pricing core takes an injected provider, so it unit-tests with a fake and
never touches the network.
"""
