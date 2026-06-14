from fastapi import APIRouter, Depends

from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas import BriefingResponse
from app.services import briefing_composer
from app.services.events import feed as events_feed
from app.services.events import summary as events_summary
from app.services.llm import briefing_ai

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("", response_model=BriefingResponse)
def get_briefing(portfolio: Portfolio = Depends(get_default_portfolio)) -> BriefingResponse:
    briefing = briefing_composer.compose_briefing(portfolio)

    # Real "what changed this week" events (news + earnings). Best-effort — a
    # data-fetch failure must never break the briefing.
    feed = None
    try:
        feed = events_feed.get_feed(portfolio)
        briefing = events_summary.apply(briefing, feed)
    except Exception:  # noqa: BLE001
        pass

    # AI narrative when configured; falls back to the deterministic briefing.
    # The feed grounds the narrative in real headlines instead of generic macro.
    briefing, _ai_used = briefing_ai.enhance(briefing, portfolio, events=feed)
    return briefing
