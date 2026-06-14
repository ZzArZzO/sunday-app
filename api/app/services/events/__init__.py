"""What-changed-this-week engine: real holdings-tagged news + earnings events.

Grounds the briefing's "what changed" section in actual data (yfinance news +
earnings calendar — no extra API key), instead of LLM-imagined events. The feed
is built per portfolio, cached daily, surfaced at GET /api/events, used to write
a deterministic "this week" section, and passed to the AI narrator for grounding.

    base.py          — NewsItem / EarningsEvent / EventsFeed + NewsProvider protocol
    yfinance_news.py — the real provider (yfinance .news + .calendar)
    feed.py          — build_feed() (pure core) + daily-cached get_feed()
    summary.py       — deterministic "what changed this week" markdown + briefing apply
"""
