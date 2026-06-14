"""Subscription state — deterministic, Stripe-free, fully unit-testable.

The webhook layer parses Stripe events and calls `apply_subscription` here; the
tier helpers are pure functions of the user's stored status.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

# Stripe subscription statuses that grant Pro access.
PRO_STATUSES = frozenset({"active", "trialing"})


def is_pro(user: User) -> bool:
    return (user.subscription_status or "") in PRO_STATUSES


def tier_for(user: User) -> str:
    return "pro" if is_pro(user) else "free"


def _to_datetime(unix_seconds: int | None) -> datetime | None:
    if not unix_seconds:
        return None
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc)


def apply_subscription(
    db: Session,
    *,
    customer_id: str,
    subscription_id: str | None,
    status: str | None,
    current_period_end: int | None,
) -> User | None:
    """Update the user matching `customer_id` with subscription state from Stripe.

    Idempotent — applying the same event twice yields the same row. Returns the
    updated user, or None if no user matches the customer (e.g. stale event).
    """
    user = db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    ).scalar_one_or_none()
    if user is None:
        return None

    user.stripe_subscription_id = subscription_id
    user.subscription_status = status
    user.subscription_period_end = _to_datetime(current_period_end)
    db.add(user)
    db.commit()
    return user
