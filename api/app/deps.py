"""FastAPI dependencies.

For the MVP slice we hardcode `demo_user_id` from settings and resolve their
default portfolio. Phase 2 swaps this for an auth-cookie-driven dependency.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Portfolio, User
from app.services.auth import tokens as auth_tokens


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    # Real auth: resolve the session cookie to a user.
    token = request.cookies.get(auth_tokens.SESSION_COOKIE)
    if token:
        user = auth_tokens.lookup_session(db, token)
        if user is not None:
            return user

    # Production requires a valid session; dev falls back to the demo user so
    # single-user testing keeps working without signing in.
    if settings.auth_required:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    user = db.get(User, settings.demo_user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (and no demo user — run the seed).",
        )
    return user


def get_default_portfolio(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Portfolio:
    portfolio = next(iter(user.portfolios), None)
    if portfolio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio for this user. Upload a CSV at POST /api/ingest.",
        )
    return portfolio
