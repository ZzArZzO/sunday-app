"""Generate → render → send the Sunday briefing, per user and for everyone."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.services import briefing_build
from app.services.billing.subscription import PRO_STATUSES
from app.services.delivery import (
    email_render,
    pdf_render,
    push_registry,
    push_sender,
    sender,
)


@dataclass(frozen=True)
class DeliveryResult:
    email: str
    ok: bool
    dry_run: bool = False
    subject: str | None = None
    message_id: str | None = None
    error: str | None = None
    # Native push, sent alongside the email when a db session is provided.
    push_sent: int = 0


@dataclass(frozen=True)
class WeeklySummary:
    total: int
    sent: int
    failed: int
    dry_run: bool
    results: list[DeliveryResult] = field(default_factory=list)


def _push_briefing(db: Session, user: User, briefing) -> int:
    """Notify all of a user's devices that the briefing is ready. Best-effort:
    push failures never affect email delivery. Returns the count delivered."""
    # Keep the body neutral — it can surface on a lock screen. The figures live
    # behind auth inside the app.
    sent = 0
    for tok in push_registry.tokens_for_user(db, user):
        res = push_sender.send_push(
            tok.token,
            "Your Sunday briefing is ready",
            "Open Sunday for this week's portfolio summary.",
            data={"kind": "weekly_briefing", "week_of": str(briefing.week_of)},
        )
        if res.ok:
            sent += 1
    return sent


def deliver_to_user(user: User, db: Session | None = None) -> DeliveryResult:
    portfolio = next(iter(user.portfolios), None)
    if portfolio is None:
        return DeliveryResult(email=user.email, ok=False, error="user has no portfolio")
    if not user.email:
        return DeliveryResult(email="", ok=False, error="user has no email")

    briefing = briefing_build.build_briefing(portfolio)
    rendered = email_render.render_briefing_email(briefing)
    pdf = pdf_render.render_briefing_pdf(briefing)
    attachments = [(f"sunday-briefing-{briefing.week_of}.pdf", pdf)]
    res = sender.send_email(
        user.email, rendered.subject, rendered.html, rendered.text, attachments=attachments
    )
    push_sent = _push_briefing(db, user, briefing) if db is not None else 0
    return DeliveryResult(
        email=user.email,
        ok=res.ok,
        dry_run=res.dry_run,
        subject=rendered.subject,
        message_id=res.message_id,
        error=res.error,
        push_sent=push_sent,
    )


def deliver_weekly(db: Session) -> WeeklySummary:
    """Send this week's briefing to every opted-in Pro user (the weekly email is Pro-only)."""
    users = list(
        db.execute(
            select(User).where(
                User.email.isnot(None),
                User.weekly_opt_in.is_(True),
                User.subscription_status.in_(PRO_STATUSES),
            )
        ).scalars()
    )
    results = [deliver_to_user(u, db) for u in users]
    return WeeklySummary(
        total=len(results),
        sent=sum(1 for r in results if r.ok),
        failed=sum(1 for r in results if not r.ok),
        dry_run=any(r.dry_run for r in results),
        results=results,
    )
