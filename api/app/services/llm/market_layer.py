"""Shared weekly market-context layer (Sonnet, cached across users).

Per docs/ARCHITECTURE.md: compute one general market read per week and reuse it
for every user's briefing — the regime/cycle/macro context is identical across
users, so it's wasteful (and inconsistent) to regenerate per person.

It's grounded in a handful of real, cheap market readings (index levels, VIX,
BTC, EUR/USD, 10y yield) fetched via the price provider, and framed as **general
information** — never advice, never invented dated events. The per-user narrative
(briefing_ai.py) consumes this as a stable, cacheable prefix.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from app.config import get_settings
from app.services.llm import cost_ledger, guardrails
from app.services.llm.client import get_client
from app.services.prices.base import PriceProvider

log = logging.getLogger(__name__)

# Cheap, reliable readings to ground the regime read. (yfinance symbols.)
_INDICATORS = (
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq Composite"),
    ("^VIX", "VIX (equity volatility)"),
    ("BTC-USD", "Bitcoin (USD)"),
    ("EURUSD=X", "EUR/USD"),
    ("^TNX", "US 10Y yield x10"),
)

_SYSTEM = """You write a brief, neutral WEEKLY MARKET CONTEXT for a calm Sunday \
investing briefing aimed at self-directed EU retail investors.

This is INFORMATION AND EDUCATION ONLY — never investment advice. Never tell \
anyone to buy, sell, hold, trim, or rebalance anything. Never predict specific \
prices. Do NOT invent specific dated news or events you weren't given — reason \
qualitatively from the readings provided.

From the current market readings, produce:
- regime_tag: a short label for the environment (e.g. "risk-on", "risk-off", \
"neutral / mixed", "elevated-volatility").
- regime_note: 2-3 plain-English sentences describing the environment and what it \
generally means, grounded in the readings (e.g. what a given VIX level implies).
- week_ahead: 2-3 sentences of general macro education on what kinds of things \
move markets in a typical week (inflation prints, central-bank meetings, earnings) \
and why — general, not a specific dated calendar.
- crypto_note: 1-2 sentences of general, educational context on the crypto market \
backdrop (heuristic, not predictive)."""


@dataclass(frozen=True)
class MarketContext:
    regime_tag: str
    regime_note: str
    week_ahead: str
    crypto_note: str
    as_of: str


class _MarketLLM(BaseModel):
    regime_tag: str
    regime_note: str
    week_ahead: str
    crypto_note: str


# Result cache: one context per ISO week, reused across all users.
_CACHE: dict[str, MarketContext] = {}


def _week_key(now: datetime) -> str:
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def _readings(provider: PriceProvider) -> str:
    lines: list[str] = []
    for symbol, label in _INDICATORS:
        try:
            q = provider.get_quote(symbol)
        except Exception:  # noqa: BLE001 - never let a reading break the briefing
            q = None
        if q is not None:
            lines.append(f"- {label}: {q.price} {q.currency}")
    return "\n".join(lines) if lines else "(no live market readings available)"


def _parse(system: str, user: str) -> _MarketLLM:
    client = get_client()
    settings = get_settings()
    resp = client.messages.parse(
        model=settings.anthropic_chat_model,  # Sonnet — the shared, higher-quality run
        max_tokens=900,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=_MarketLLM,
    )
    # Shared across all users (once per ISO week) → log with no user attribution.
    cost_ledger.record_response("market_layer", resp, user_id=None)
    return resp.parsed_output


def compute(provider: PriceProvider, now: datetime) -> MarketContext:
    """Generate the market context (one Sonnet call). Raises on hard failure."""
    user = (
        f"Current market readings as of {now.date().isoformat()}:\n"
        f"{_readings(provider)}\n\nWrite the weekly market context."
    )
    out = _parse(_SYSTEM, user)

    blob = "\n".join([out.regime_note, out.week_ahead, out.crypto_note])
    if not guardrails.scan(blob).clean:
        out = _parse(_SYSTEM + "\n\n" + guardrails.STRICTER_REPROMPT, user)
        blob = "\n".join([out.regime_note, out.week_ahead, out.crypto_note])
        if not guardrails.scan(blob).clean:
            raise ValueError("market context tripped the advice guardrail twice")

    return MarketContext(
        regime_tag=out.regime_tag,
        regime_note=out.regime_note,
        week_ahead=out.week_ahead,
        crypto_note=out.crypto_note,
        as_of=now.isoformat(),
    )


def get_market_context(provider: PriceProvider, now: datetime) -> MarketContext:
    """Weekly-cached market context — computed once per ISO week, reused for all users."""
    key = _week_key(now)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    ctx = compute(provider, now)
    _CACHE[key] = ctx
    return ctx
