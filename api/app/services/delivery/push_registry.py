"""Storage for device push tokens — register (upsert), list, unregister."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PushToken, User

_PLATFORMS = {"ios", "android", "web"}
# Cap devices per user so a token can't be used to grow the table (or amplify
# /push/test) without bound. Beyond this, the least-recently-seen device is evicted.
MAX_TOKENS_PER_USER = 10


def register_token(
    db: Session, user: User, token: str, platform: str, *, now: datetime | None = None
) -> PushToken:
    """Upsert a device token for a user.

    A token uniquely identifies one app install (FCM guarantees this), so an
    existing token re-registering is the same device — reinstall, rotation, or a
    new account signing in on that device. We point it at the current user and
    bump `last_seen_at`; the row is never duplicated.
    """
    now = now or datetime.now(timezone.utc)
    platform = platform if platform in _PLATFORMS else "android"

    row = db.execute(
        select(PushToken).where(PushToken.token == token)
    ).scalar_one_or_none()
    if row is None:
        row = PushToken(user_id=user.id, token=token, platform=platform, last_seen_at=now)
        db.add(row)
        db.flush()
        _evict_over_cap(db, user, now)
    else:
        row.user_id = user.id
        row.platform = platform
        row.last_seen_at = now
        db.flush()
    return row


def _evict_over_cap(db: Session, user: User, now: datetime) -> None:
    rows = list(
        db.execute(
            select(PushToken)
            .where(PushToken.user_id == user.id)
            .order_by(PushToken.last_seen_at.desc())
        ).scalars()
    )
    for stale in rows[MAX_TOKENS_PER_USER:]:
        db.delete(stale)
    if len(rows) > MAX_TOKENS_PER_USER:
        db.flush()


def tokens_for_user(db: Session, user: User) -> list[PushToken]:
    return list(
        db.execute(select(PushToken).where(PushToken.user_id == user.id)).scalars()
    )


def unregister_token(db: Session, user: User, token: str) -> bool:
    """Remove one of the *current user's* tokens. Scoped by user so a caller can't
    delete (silence) another user's device. Returns True if a row was removed."""
    row = db.execute(
        select(PushToken).where(
            PushToken.token == token, PushToken.user_id == user.id
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    db.delete(row)
    db.flush()
    return True
