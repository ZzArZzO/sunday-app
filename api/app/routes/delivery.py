"""Briefing delivery endpoints.

POST /api/delivery/briefing — send the current user their briefing now.
POST /api/delivery/weekly   — send everyone this week's briefing (what the cron calls).

Both render + send via Resend, or dry-run when no RESEND_API_KEY is set.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.delivery import (
    DeliveryPreferencesUpdate,
    DeliveryPreferencesView,
    DeliveryResultView,
    WeeklyDeliverySummary,
)
from app.services.billing import subscription
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


@router.get("/preferences", response_model=DeliveryPreferencesView)
def get_preferences(user: User = Depends(get_current_user)) -> DeliveryPreferencesView:
    return DeliveryPreferencesView(
        weekly_opt_in=user.weekly_opt_in, is_pro=subscription.is_pro(user)
    )


@router.put("/preferences", response_model=DeliveryPreferencesView)
def update_preferences(
    update: DeliveryPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeliveryPreferencesView:
    # The weekly Sunday email is a Pro feature; free users can't opt in.
    if update.weekly_opt_in and not subscription.is_pro(user):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="The weekly Sunday email is a Pro feature. Upgrade to receive it every week.",
        )
    user.weekly_opt_in = update.weekly_opt_in
    db.add(user)
    db.commit()
    return DeliveryPreferencesView(
        weekly_opt_in=user.weekly_opt_in, is_pro=subscription.is_pro(user)
    )


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
