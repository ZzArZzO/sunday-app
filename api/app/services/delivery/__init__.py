"""Delivery layer — the "Sunday briefing in your inbox" promise.

    markdown_lite.py      — tiny, safe markdown→HTML for the briefing bodies
    email_render.py       — BriefingResponse → calm HTML + plain-text email
    sender.py             — send via Resend, or dry-run when no key is configured
    briefing_delivery.py  — generate + render + send per user / for everyone
    scheduler.py          — weekly Sunday cron (opt-in)
"""
