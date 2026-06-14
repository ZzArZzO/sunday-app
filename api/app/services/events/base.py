"""Event types and the provider boundary for the what-changed engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class NewsItem:
    holding: str  # the user's ticker this news is tagged to (set by the feed)
    title: str
    summary: str
    publisher: str | None
    url: str | None
    published_at: datetime | None


@dataclass(frozen=True)
class EarningsEvent:
    ticker: str
    date: date


@dataclass(frozen=True)
class EventsFeed:
    as_of: str
    news: list[NewsItem] = field(default_factory=list)
    earnings: list[EarningsEvent] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class NewsProvider(Protocol):
    def get_news(self, symbol: str) -> list[NewsItem]:
        """Recent news for a market symbol (holding left blank; the feed tags it)."""
        ...

    def get_earnings_date(self, symbol: str) -> date | None:
        """Next scheduled earnings date for a symbol, if any."""
        ...
