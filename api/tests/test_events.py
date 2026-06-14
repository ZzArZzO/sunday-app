"""Tests for the what-changed-this-week engine (services/events).

Pure and deterministic — a fake provider stands in for yfinance, so nothing hits
the network. Covers windowing/dedup/tagging, earnings horizon, the markdown
summary, and applying it to a briefing.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.models import Position
from app.schemas import BriefingResponse, BriefingSection
from app.schemas.portfolio import DualMoney
from app.services.events import summary as events_summary
from app.services.events.base import NewsItem
from app.services.events.feed import build_feed

NOW = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)


def _pos(ticker: str, asset_class: str = "stock", isin: str | None = None) -> Position:
    return Position(
        id=abs(hash(ticker)) % 100000,
        ticker=ticker,
        asset_class=asset_class,
        isin=isin,
        quantity=Decimal("1"),
        avg_cost_eur=Decimal("1"),
    )


def _news(title: str, days_ago: float = 1, publisher: str = "Pub") -> NewsItem:
    return NewsItem(
        holding="",
        title=title,
        summary="",
        publisher=publisher,
        url="http://example.com",
        published_at=NOW - timedelta(days=days_ago),
    )


class FakeProvider:
    def __init__(self, news=None, earnings=None):
        self._news = news or {}
        self._earnings = earnings or {}

    def get_news(self, symbol):
        return list(self._news.get(symbol, []))

    def get_earnings_date(self, symbol):
        return self._earnings.get(symbol)


class TestBuildFeed:
    def test_windows_dedups_tags_and_filters_earnings(self):
        provider = FakeProvider(
            news={
                "AAPL": [_news("Apple A", 1), _news("Apple A", 2), _news("Apple Old", 30)],
                "MSFT": [_news("MS B", 3)],
            },
            earnings={
                "AAPL": date(2026, 6, 20),   # within 21-day horizon
                "MSFT": date(2026, 8, 1),    # outside horizon
            },
        )
        portfolio = SimpleNamespace(id=1, positions=[_pos("AAPL"), _pos("MSFT")])
        feed = build_feed(portfolio, provider, now=NOW)

        titles = {n.title for n in feed.news}
        assert titles == {"Apple A", "MS B"}            # dup collapsed, 30d-old dropped
        tags = {n.title: n.holding for n in feed.news}
        assert tags["Apple A"] == "AAPL" and tags["MS B"] == "MSFT"

        assert [e.ticker for e in feed.earnings] == ["AAPL"]  # MSFT beyond horizon
        assert feed.earnings[0].date == date(2026, 6, 20)

    def test_crypto_gets_news_but_no_earnings(self):
        # candidate symbols for crypto are BTC-EUR then BTC-USD.
        provider = FakeProvider(
            news={"BTC-USD": [_news("Bitcoin rallies", 1)]},
            earnings={"BTC-USD": date(2026, 6, 18)},  # should be ignored for crypto
        )
        portfolio = SimpleNamespace(id=1, positions=[_pos("BTC", asset_class="crypto")])
        feed = build_feed(portfolio, provider, now=NOW)

        assert [n.holding for n in feed.news] == ["BTC"]
        assert feed.earnings == []


class TestSummary:
    def _feed_with_content(self):
        portfolio = SimpleNamespace(id=1, positions=[_pos("AAPL")])
        provider = FakeProvider(
            news={"AAPL": [_news("Apple ships chips", 1, publisher="Reuters")]},
            earnings={"AAPL": date(2026, 6, 20)},
        )
        return build_feed(portfolio, provider, now=NOW)

    def test_markdown_empty_feed(self):
        empty = build_feed(SimpleNamespace(id=1, positions=[]), FakeProvider(), now=NOW)
        body = events_summary.what_changed_markdown(empty)
        assert "No major headlines" in body

    def test_markdown_with_content(self):
        body = events_summary.what_changed_markdown(self._feed_with_content())
        assert "Earnings coming up" in body
        assert "AAPL" in body and "2026-06-20" in body
        assert "Apple ships chips" in body and "Reuters" in body

    def test_facts_block(self):
        assert events_summary.facts_block(build_feed(SimpleNamespace(id=1, positions=[]), FakeProvider(), now=NOW)) == ""
        block = events_summary.facts_block(self._feed_with_content())
        assert "AAPL earnings on 2026-06-20" in block
        assert "[AAPL] Apple ships chips" in block

    def test_apply_replaces_what_changed_section(self):
        dm = DualMoney(eur=Decimal("0"), usd=Decimal("0"))
        briefing = BriefingResponse(
            portfolio_id=1, week_of="2026-06-14", generated_at="t", fx_eur_usd=Decimal("1.1"),
            net_worth=dm, wow_delta=dm, wow_delta_pct=Decimal("0"), wow_available=False,
            wow_baseline_date=None,
            sections=[
                BriefingSection(kind="what_changed", title="x", body_markdown="PLACEHOLDER"),
                BriefingSection(kind="tax_flags", title="Tax", body_markdown="TAX"),
            ],
            concentration_alerts=[],
        )
        out = events_summary.apply(briefing, self._feed_with_content())
        by_kind = {s.kind: s for s in out.sections}
        assert "Apple ships chips" in by_kind["what_changed"].body_markdown
        assert by_kind["what_changed"].title == "What changed this week"
        assert by_kind["tax_flags"].body_markdown == "TAX"  # untouched
