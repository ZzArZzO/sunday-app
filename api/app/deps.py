"""FastAPI dependencies.

Auth is Bearer-JWT-only: the frontend (web or mobile) sends
`Authorization: Bearer <supabase_access_token>` and this dependency verifies
it against Supabase's JWKS (see services/auth/supabase_jwt.py) — no cookie,
no server-side session table.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Portfolio, User
from app.services.auth import supabase_jwt
from app.services.auth import users as auth_users


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    token = supabase_jwt.bearer_token_from_request(request)
    if token:
        claims = supabase_jwt.verify_access_token(token)
        if claims is not None and claims.email:
            return auth_users.get_or_create_user_from_supabase(db, claims.user_id, claims.email)

    # Production requires a valid session; dev falls back to the demo user so
    # single-user testing keeps working without signing in. Preserved verbatim
    # from the pre-Supabase auth system — this is the local-dev escape hatch,
    # not part of the Supabase-auth path above.
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
