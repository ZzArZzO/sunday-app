"""Magic-link tokens and login sessions.

Only token *hashes* are stored; the plaintext lives in the email link / cookie.
Datetimes are normalised to aware-UTC on read so comparisons work the same on
Postgres (tz-aware) and SQLite (naive) — the test DB.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MagicToken, User, UserSession

SESSION_COOKIE = "sunday_session"
MAGIC_TTL_MINUTES = 15
SESSION_TTL_DAYS = 30


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_token() -> str:
    return secrets.token_urlsafe(32)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def create_magic_token(
    db: Session, user: User, *, now: datetime | None = None, ttl_minutes: int = MAGIC_TTL_MINUTES
) -> str:
    now = now or datetime.now(timezone.utc)
    token = _new_token()
    db.add(
        MagicToken(
            user_id=user.id,
            token_hash=_hash(token),
            expires_at=now + timedelta(minutes=ttl_minutes),
        )
    )
    db.flush()
    return token


def consume_magic_token(db: Session, token: str, *, now: datetime | None = None) -> User | None:
    """Validate + single-use-consume a magic token; return its user or None."""
    now = now or datetime.now(timezone.utc)
    row = db.execute(
        select(MagicToken).where(MagicToken.token_hash == _hash(token))
    ).scalar_one_or_none()
    if row is None or row.used_at is not None or _aware(row.expires_at) < now:
        return None
    row.used_at = now
    db.flush()
    return db.get(User, row.user_id)


def create_session(
    db: Session, user: User, *, now: datetime | None = None, ttl_days: int = SESSION_TTL_DAYS
) -> str:
    now = now or datetime.now(timezone.utc)
    token = _new_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=_hash(token),
            expires_at=now + timedelta(days=ttl_days),
        )
    )
    db.flush()
    return token


def lookup_session(db: Session, token: str, *, now: datetime | None = None) -> User | None:
    if not token:
        return None
    now = now or datetime.now(timezone.utc)
    row = db.execute(
        select(UserSession).where(UserSession.token_hash == _hash(token))
    ).scalar_one_or_none()
    if row is None or _aware(row.expires_at) < now:
        return None
    return db.get(User, row.user_id)


def session_token_from_request(request) -> str | None:
    """Extract the session token from a request.

    `Authorization: Bearer <token>` (mobile / Capacitor) takes precedence; the
    session cookie (web) is the fallback. Duck-typed so it works with both a real
    Starlette Request and a lightweight test stand-in.
    """
    header = request.headers.get("Authorization")
    if header and header[:7].lower() == "bearer ":
        candidate = header[7:].strip()
        if candidate:
            return candidate
    return request.cookies.get(SESSION_COOKIE)


def revoke_session(db: Session, token: str) -> None:
    if not token:
        return
    row = db.execute(
        select(UserSession).where(UserSession.token_hash == _hash(token))
    ).scalar_one_or_none()
    if row is not None:
        db.delete(row)
        db.flush()
