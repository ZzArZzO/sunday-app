"""Generate → render → send the Sunday briefing, per user and for everyone."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.services import briefing_build
from app.services.delivery import email_render, sender


@dataclass(frozen=True)
class DeliveryResult:
    email: str
    ok: bool
    dry_run: bool = False
    subject: str | None = None
    message_id: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class WeeklySummary:
    total: int
    sent: int
    failed: int
    dry_run: bool
    results: list[DeliveryResult] = field(default_factory=list)


def deliver_to_user(user: User) -> DeliveryResult:
    portfolio = next(iter(user.portfolios), None)
    if portfolio is None:
        return DeliveryResult(email=user.email, ok=False, error="user has no portfolio")
    if not user.email:
        return DeliveryResult(email="", ok=False, error="user has no email")

    briefing = briefing_build.build_briefing(portfolio)
    rendered = email_render.render_briefing_email(briefing)
    res = sender.send_email(user.email, rendered.subject, rendered.html, rendered.text)
    return DeliveryResult(
        email=user.email,
        ok=res.ok,
        dry_run=res.dry_run,
        subject=rendered.subject,
        message_id=res.message_id,
        error=res.error,
    )


def deliver_weekly(db: Session) -> WeeklySummary:
    """Send this week's briefing to every user with an email address."""
    users = list(db.execute(select(User).where(User.email.isnot(None))).scalars())
    results = [deliver_to_user(u) for u in users]
    return WeeklySummary(
        total=len(results),
        sent=sum(1 for r in results if r.ok),
        failed=sum(1 for r in results if not r.ok),
        dry_run=any(r.dry_run for r in results),
        results=results,
    )
