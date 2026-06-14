"""Assemble the full briefing: deterministic compose → real events → AI narrative.

Single source of truth used by both the GET /api/briefing route and the email
delivery layer, so an emailed briefing is identical to the in-app one.
"""

from __future__ import annotations

from app.models import Portfolio
from app.schemas import BriefingResponse
from app.services import briefing_composer
from app.services.events import feed as events_feed
from app.services.events import summary as events_summary
from app.services.llm import briefing_ai


def build_briefing(portfolio: Portfolio) -> BriefingResponse:
    briefing = briefing_composer.compose_briefing(portfolio)

    # Real "what changed this week" events — best-effort, never breaks the briefing.
    feed = None
    try:
        feed = events_feed.get_feed(portfolio)
        briefing = events_summary.apply(briefing, feed)
    except Exception:  # noqa: BLE001
        feed = None

    # AI narrative when configured; deterministic fallback otherwise.
    briefing, _ai_used = briefing_ai.enhance(briefing, portfolio, events=feed)
    return briefing
