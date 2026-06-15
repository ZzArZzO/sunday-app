"""Monthly per-user AI budget cap — the margin backstop.

Reads month-to-date AI spend from the `llm_call_log` ledger and compares it to
the user's tier cap. Once exhausted, callers degrade gracefully (chat returns a
calm allowance message; the briefing falls back to its deterministic narrative)
until the calendar month rolls over. The numbers and dashboard are never gated.

Caps are USD (the ledger's currency) and configurable per tier in settings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import LlmCallLog, User
from app.services.billing import subscription

ALLOWANCE_MESSAGE = (
    "You've reached your monthly AI allowance, so I can't generate a new answer "
    "right now. It resets on the 1st. Your dashboard, holdings, and briefing "
    "numbers are all still fully available in the meantime."
)


def monthly_cap_usd(user: User) -> Decimal:
    s = get_settings()
    cap = s.ai_monthly_budget_pro_usd if subscription.is_pro(user) else s.ai_monthly_budget_free_usd
    return Decimal(str(cap))


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def month_to_date_usd(db: Session, user_id: int | None) -> Decimal:
    """Sum of this user's AI spend since the 1st of the current month."""
    if user_id is None:
        return Decimal("0")
    since = _month_start(datetime.now(timezone.utc))
    total = db.execute(
        select(func.coalesce(func.sum(LlmCallLog.cost_usd), 0)).where(
            LlmCallLog.user_id == user_id, LlmCallLog.created_at >= since
        )
    ).scalar_one()
    return Decimal(str(total))


def status(db: Session, user: User) -> dict:
    cap = monthly_cap_usd(user)
    spent = month_to_date_usd(db, user.id)
    remaining = cap - spent
    return {
        "cap_usd": cap,
        "spent_usd": spent,
        "remaining_usd": remaining if remaining > Decimal("0") else Decimal("0"),
        "exhausted": spent >= cap,
    }


def is_exhausted(db: Session, user: User) -> bool:
    return month_to_date_usd(db, user.id) >= monthly_cap_usd(user)
