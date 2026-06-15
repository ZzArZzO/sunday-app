"""Device push-notification registration.

    POST /api/push/register    {token, platform}  → store this device's token
    POST /api/push/unregister  {token}            → forget a device's token
    POST /api/push/test                           → send a test push to my devices

The mobile app calls /register after the OS grants notification permission. The
weekly Sunday briefing then fans out to every registered device (see
`briefing_delivery`). Without FCM credentials the send is a dry-run.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.push import (
    PushTestResponse,
    RegisterPushRequest,
    RegisterPushResponse,
    UnregisterPushRequest,
)
from app.services.delivery import push_registry, push_sender

router = APIRouter(prefix="/api/push", tags=["push"])


@router.post("/register", response_model=RegisterPushResponse)
def register(
    body: RegisterPushRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RegisterPushResponse:
    push_registry.register_token(db, user, body.token, body.platform)
    db.commit()
    return RegisterPushResponse(ok=True)


@router.post("/unregister", status_code=status.HTTP_204_NO_CONTENT)
def unregister(
    body: UnregisterPushRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    push_registry.unregister_token(db, user, body.token)
    db.commit()


@router.post("/test", response_model=PushTestResponse)
def test_push(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PushTestResponse:
    """Send a test notification to all of the current user's devices."""
    tokens = push_registry.tokens_for_user(db, user)
    results = [
        push_sender.send_push(
            t.token,
            "Sunday",
            "Push notifications are on — your weekly briefing will land here.",
            data={"kind": "test"},
        )
        for t in tokens
    ]
    return PushTestResponse(
        sent=sum(1 for r in results if r.ok),
        dry_run=any(r.dry_run for r in results),
    )
