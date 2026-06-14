"""Real news + earnings provider, backed by yfinance.

yfinance `.news` items are `{id, content:{title, summary, pubDate, provider,
canonicalUrl, ...}}`; earnings come from `.calendar['Earnings Date']` (a list of
dates). Both are free and need no extra API key. All access is defensive — a
malformed item or a network hiccup yields no events, never an exception that
could break the briefing.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from app.services.events.base import NewsItem
from app.services.prices.yfinance_provider import get_yf

log = logging.getLogger(__name__)


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


class YFinanceNewsProvider:
    def get_news(self, symbol: str) -> list[NewsItem]:
        if not symbol:
            return []
        try:
            raw = get_yf().Ticker(symbol).news or []
        except Exception as exc:  # noqa: BLE001 - never break on a news fetch
            log.warning("news fetch failed for %s: %s", symbol, exc)
            return []

        items: list[NewsItem] = []
        for entry in raw:
            content = (entry or {}).get("content") or {}
            content_type = content.get("contentType")
            if content_type not in (None, "STORY"):
                continue
            title = (content.get("title") or "").strip()
            if not title:
                continue
            items.append(
                NewsItem(
                    holding="",  # tagged by the feed
                    title=title,
                    summary=(content.get("summary") or content.get("description") or "").strip(),
                    publisher=((content.get("provider") or {}).get("displayName")),
                    url=(
                        (content.get("canonicalUrl") or {}).get("url")
                        or (content.get("clickThroughUrl") or {}).get("url")
                    ),
                    published_at=_parse_dt(content.get("pubDate") or content.get("displayTime")),
                )
            )
        return items

    def get_earnings_date(self, symbol: str) -> date | None:
        if not symbol:
            return None
        try:
            calendar = get_yf().Ticker(symbol).calendar or {}
        except Exception as exc:  # noqa: BLE001
            log.warning("calendar fetch failed for %s: %s", symbol, exc)
            return None
        dates = calendar.get("Earnings Date") or []
        future = sorted(d for d in dates if isinstance(d, date))
        return future[0] if future else None
