"""Build the per-portfolio events feed (real news + upcoming earnings).

`build_feed` is the pure core: given the portfolio + a news provider, it gathers
recent news per holding (windowed, de-duplicated, tagged) and near-term earnings
dates. `get_feed` wraps it with a once-per-day cache and the real yfinance
provider so the briefing doesn't refetch on every view.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime, timedelta, timezone

from app.models import Portfolio
from app.services.events.base import EarningsEvent, EventsFeed, NewsItem, NewsProvider
from app.services.events.yfinance_news import YFinanceNewsProvider
from app.services.prices.symbols import candidate_symbols

log = logging.getLogger(__name__)

_NEWS_WINDOW_DAYS = 7
_EARNINGS_HORIZON_DAYS = 21
_MAX_NEWS = 8
_MAX_NEWS_SYMBOLS = 2  # bound network: try at most the top 2 candidate symbols


def _news_symbols(position) -> list[str]:
    return candidate_symbols(position)[:_MAX_NEWS_SYMBOLS]


def build_feed(
    portfolio: Portfolio,
    provider: NewsProvider,
    *,
    now: datetime,
    window_days: int = _NEWS_WINDOW_DAYS,
    earnings_horizon_days: int = _EARNINGS_HORIZON_DAYS,
    max_news: int = _MAX_NEWS,
) -> EventsFeed:
    positions = list(portfolio.positions)
    cutoff = now - timedelta(days=window_days)
    horizon = (now + timedelta(days=earnings_horizon_days)).date()

    news: list[NewsItem] = []
    earnings: list[EarningsEvent] = []
    seen_titles: set[str] = set()

    for position in positions:
        symbols = _news_symbols(position)

        # News: take the first candidate symbol that returns anything.
        for symbol in symbols:
            items = provider.get_news(symbol)
            if not items:
                continue
            for item in items:
                if item.published_at is not None and item.published_at < cutoff:
                    continue
                key = item.title.strip().lower()
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                news.append(dataclasses.replace(item, holding=position.ticker))
            break

        # Earnings: equities/ETFs only, within the horizon.
        if position.asset_class != "crypto" and symbols:
            earnings_date = provider.get_earnings_date(symbols[0])
            if earnings_date and now.date() <= earnings_date <= horizon:
                earnings.append(EarningsEvent(ticker=position.ticker, date=earnings_date))

    news.sort(key=lambda n: n.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    earnings.sort(key=lambda e: e.date)

    return EventsFeed(as_of=now.isoformat(), news=news[:max_news], earnings=earnings, notes=[])


# Cache one feed per (portfolio, calendar day).
_FEED_CACHE: dict[tuple[int, str], EventsFeed] = {}


def get_feed(portfolio: Portfolio, *, now: datetime | None = None) -> EventsFeed:
    now = now or datetime.now(timezone.utc)
    key = (portfolio.id, now.date().isoformat())
    cached = _FEED_CACHE.get(key)
    if cached is not None:
        return cached
    feed = build_feed(portfolio, YFinanceNewsProvider(), now=now)
    _FEED_CACHE[key] = feed
    return feed
