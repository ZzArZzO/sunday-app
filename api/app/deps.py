"""FastAPI dependencies.

For the MVP slice we hardcode `demo_user_id` from settings and resolve their
default portfolio. Phase 2 swaps this for an auth-cookie-driven dependency.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Portfolio, User


def get_current_user(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    user = db.get(User, settings.demo_user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo user not found. Run `python -m app.seeds.load_sample` first.",
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
