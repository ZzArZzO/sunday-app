"""What-changed-this-week events feed.

GET /api/events — real holdings-tagged news + near-term earnings for the
portfolio (yfinance; cached once per day). Also drives the briefing's
"what changed" section.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas.events import EarningsEventView, EventsResponse, NewsItemView
from app.services.events import feed as events_feed
from app.services.prices.base import PricesUnavailable

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventsResponse)
def get_events(portfolio: Portfolio = Depends(get_default_portfolio)) -> EventsResponse:
    try:
        feed = events_feed.get_feed(portfolio)
    except PricesUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return EventsResponse(
        as_of=feed.as_of,
        news=[
            NewsItemView(
                holding=n.holding,
                title=n.title,
                summary=n.summary,
                publisher=n.publisher,
                url=n.url,
                published_at=n.published_at.isoformat() if n.published_at else None,
            )
            for n in feed.news
        ],
        earnings=[EarningsEventView(ticker=e.ticker, date=e.date.isoformat()) for e in feed.earnings],
        notes=feed.notes,
    )
