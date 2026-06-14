"""Render the events feed into the briefing's "what changed this week" section.

`what_changed_markdown` is the deterministic body (shown even with no AI key);
`facts_block` is a compact, LLM-facing version the AI narrator uses for grounding
so its prose references real headlines instead of inventing them.
"""

from __future__ import annotations

from app.schemas import BriefingResponse
from app.services.events.base import EventsFeed

_EMPTY = (
    "No major headlines on your holdings in the past week, and no earnings from "
    "your holdings are scheduled in the next few weeks."
)


def what_changed_markdown(feed: EventsFeed) -> str:
    if not feed.news and not feed.earnings:
        return _EMPTY

    blocks: list[str] = []
    if feed.earnings:
        lines = "\n".join(
            f"- **{e.ticker}** reports on {e.date.isoformat()}" for e in feed.earnings
        )
        blocks.append("**Earnings coming up:**\n\n" + lines)
    if feed.news:
        lines_list = []
        for n in feed.news:
            when = n.published_at.date().isoformat() if n.published_at else ""
            src = f"{n.publisher}" if n.publisher else ""
            meta = " · ".join(x for x in (when, src) if x)
            suffix = f" ({meta})" if meta else ""
            lines_list.append(f"- **{n.holding}** — {n.title}{suffix}")
        blocks.append("**Headlines on your holdings this week:**\n\n" + "\n".join(lines_list))
    return "\n\n".join(blocks)


def facts_block(feed: EventsFeed) -> str:
    """Compact, LLM-facing event list for grounding the narrative (or '' if none)."""
    if not feed.news and not feed.earnings:
        return ""
    parts = ["RECENT EVENTS (real, from market data — use these, do not invent others):"]
    for e in feed.earnings:
        parts.append(f"- {e.ticker} earnings on {e.date.isoformat()}")
    for n in feed.news[:6]:
        when = n.published_at.date().isoformat() if n.published_at else ""
        parts.append(f"- [{n.holding}] {n.title}" + (f" ({when})" if when else ""))
    return "\n".join(parts)


def apply(briefing: BriefingResponse, feed: EventsFeed) -> BriefingResponse:
    """Replace the deterministic what_changed body with the real events summary."""
    body = what_changed_markdown(feed)
    sections = [
        s.model_copy(update={"body_markdown": body, "title": "What changed this week"})
        if s.kind == "what_changed"
        else s
        for s in briefing.sections
    ]
    return briefing.model_copy(update={"sections": sections})
