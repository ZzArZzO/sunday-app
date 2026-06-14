"""Briefing delivery endpoints.

POST /api/delivery/briefing — send the current user their briefing now.
POST /api/delivery/weekly   — send everyone this week's briefing (what the cron calls).

Both render + send via Resend, or dry-run when no RESEND_API_KEY is set.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.delivery import DeliveryResultView, WeeklyDeliverySummary
from app.services.delivery import briefing_delivery

router = APIRouter(prefix="/api/delivery", tags=["delivery"])


def _to_view(result: briefing_delivery.DeliveryResult) -> DeliveryResultView:
    return DeliveryResultView(
        email=result.email,
        ok=result.ok,
        dry_run=result.dry_run,
        subject=result.subject,
        message_id=result.message_id,
        error=result.error,
    )


@router.post("/briefing", response_model=DeliveryResultView)
def send_my_briefing(user: User = Depends(get_current_user)) -> DeliveryResultView:
    return _to_view(briefing_delivery.deliver_to_user(user))


@router.post("/weekly", response_model=WeeklyDeliverySummary)
def send_weekly(db: Session = Depends(get_db)) -> WeeklyDeliverySummary:
    summary = briefing_delivery.deliver_weekly(db)
    return WeeklyDeliverySummary(
        total=summary.total,
        sent=summary.sent,
        failed=summary.failed,
        dry_run=summary.dry_run,
        results=[_to_view(r) for r in summary.results],
    )
