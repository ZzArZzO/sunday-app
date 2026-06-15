"""Per-user briefing narrative (Haiku) — the AI layer of the Sunday briefing.

Turns the *deterministic* briefing (real numbers: net worth, week-over-week,
allocation, holdings) plus the shared weekly market context into warm,
plain-English prose for the two sections that are otherwise placeholders:
`what_changed` ("this week") and `regime`.

Hard rules (docs/ARCHITECTURE.md + docs/LEGAL.md):
- The model writes ONLY prose; every number comes from the deterministic layer.
- Output passes the MiFID II forbidden-phrase guardrail; one stricter retry,
  then fall back to the deterministic body.
- If there's no API key, or anything errors, `enhance` returns the deterministic
  briefing unchanged — the briefing must never break.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel

from app.config import get_settings
from app.models import Portfolio
from app.schemas import BriefingResponse
from app.services.events import summary as events_summary
from app.services.events.base import EventsFeed
from app.services.llm import cost_ledger, guardrails, market_layer, portfolio_context
from app.services.llm.client import get_client
from app.services.prices.yfinance_provider import YFinanceProvider

log = logging.getLogger(__name__)

_SYSTEM = """You write two short sections of a calm Sunday portfolio briefing for \
a self-directed EU retail investor.

INFORMATION AND EDUCATION ONLY — never investment advice. Never tell them to buy, \
sell, hold, trim, add to, or rebalance anything; never use "you should"; never \
predict prices; never invent specific dated news or events.

You are given (a) the user's PORTFOLIO FACTS with exact numbers and (b) a general \
WEEKLY MARKET CONTEXT. Write:
- this_week: 2-4 warm, plain-English sentences on what's worth understanding this \
week for THIS portfolio — connect the general market context to the user's actual \
asset mix and notable holdings. Describe and contextualise; do not direct.
- regime: 2-3 neutral, educational sentences on the current market environment \
(from the provided context) and what that generally means for a mix like theirs.

Use only numbers you were given; when unsure, stay general. You are an AI; the \
user has been told this."""


@dataclass(frozen=True)
class NarrativeOut:
    this_week: str
    regime: str


class _NarrativeLLM(BaseModel):
    this_week: str
    regime: str


# Per (portfolio, ISO week) cache so repeated briefing views reuse one Haiku call.
_NARRATIVE_CACHE: dict[tuple[int, str], NarrativeOut] = {}


def _accept(n: NarrativeOut) -> bool:
    """A narrative is usable only if both sections are non-empty and advice-free."""
    if not n.this_week.strip() or not n.regime.strip():
        return False
    return guardrails.scan(f"{n.this_week}\n{n.regime}").clean


def _facts(
    response: BriefingResponse, portfolio: Portfolio, events: EventsFeed | None = None
) -> str:
    snapshot = portfolio_context.build_snapshot(portfolio)
    if response.wow_available:
        baseline = f", since {response.wow_baseline_date}" if response.wow_baseline_date else ""
        wow = f"\n- Week over week: {response.wow_delta_pct}% (€{response.wow_delta.eur}){baseline}."
    else:
        wow = "\n- Week-over-week: not enough history yet to compare."
    facts = snapshot + wow
    if events is not None:
        block = events_summary.facts_block(events)
        if block:
            facts += "\n\n" + block
    return facts


def _generate(
    facts: str,
    ctx: market_layer.MarketContext,
    *,
    strict: bool = False,
    user_id: int | None = None,
    portfolio_id: int | None = None,
) -> NarrativeOut:
    client = get_client()
    settings = get_settings()
    market_block = (
        f"WEEKLY MARKET CONTEXT (regime: {ctx.regime_tag}).\n"
        f"{ctx.regime_note}\n\nWeek ahead: {ctx.week_ahead}\n\nCrypto backdrop: {ctx.crypto_note}"
    )
    system = [
        {"type": "text", "text": _SYSTEM + (("\n\n" + guardrails.STRICTER_REPROMPT) if strict else "")},
        # Stable across all users this week → cacheable prefix.
        {"type": "text", "text": market_block, "cache_control": {"type": "ephemeral"}},
    ]
    resp = client.messages.parse(
        model=settings.anthropic_guard_model,  # Haiku — cheap per-user pass
        max_tokens=700,
        system=system,
        messages=[{"role": "user", "content": facts + "\n\nWrite the two sections."}],
        output_format=_NarrativeLLM,
    )
    cost_ledger.record_response(
        "briefing_narrative", resp, user_id=user_id, portfolio_id=portfolio_id
    )
    out = resp.parsed_output
    narrative = NarrativeOut(this_week=out.this_week.strip(), regime=out.regime.strip())
    if not strict and not _accept(narrative):
        # one stricter retry
        return _generate(facts, ctx, strict=True, user_id=user_id, portfolio_id=portfolio_id)
    return narrative


def apply_narrative(response: BriefingResponse, narrative: NarrativeOut) -> BriefingResponse:
    """Pure: replace the two placeholder section bodies and mark AI assistance."""
    sections = []
    for section in response.sections:
        if section.kind == "what_changed":
            sections.append(section.model_copy(update={"body_markdown": narrative.this_week}))
        elif section.kind == "regime":
            sections.append(section.model_copy(update={"body_markdown": narrative.regime}))
        else:
            sections.append(section)

    disclaimers = list(response.disclaimers)
    if "Generated with AI assistance." not in disclaimers:
        disclaimers.append("Generated with AI assistance.")

    return response.model_copy(update={"sections": sections, "disclaimers": disclaimers})


def enhance(
    response: BriefingResponse,
    portfolio: Portfolio,
    *,
    now: datetime | None = None,
    events: EventsFeed | None = None,
) -> tuple[BriefingResponse, bool]:
    """Add the AI narrative if possible; otherwise return the deterministic briefing.

    Returns (response, ai_used). Never raises — the briefing must always render.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        return response, False

    now = now or datetime.now(timezone.utc)
    cache_key = (portfolio.id, market_layer._week_key(now))

    cached = _NARRATIVE_CACHE.get(cache_key)
    if cached is not None:
        return apply_narrative(response, cached), True

    try:
        provider = YFinanceProvider()
        ctx = market_layer.get_market_context(provider, now)
        narrative = _generate(
            _facts(response, portfolio, events),
            ctx,
            user_id=portfolio.user_id,
            portfolio_id=portfolio.id,
        )
    except Exception as exc:  # noqa: BLE001 - any failure → deterministic briefing
        log.warning("briefing AI enhancement skipped: %s", exc)
        return response, False

    if not _accept(narrative):
        return response, False

    _NARRATIVE_CACHE[cache_key] = narrative
    return apply_narrative(response, narrative), True
