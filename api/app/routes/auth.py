"""Account endpoints that sit alongside Supabase Auth.

Supabase's hosted GoTrue service handles sign-up, sign-in (password, OTP,
OAuth), and MFA directly from the frontend — this router only covers what
Supabase's session object doesn't know about (the app's own `country` field)
plus a graceful "am I signed in" check for the frontend to call without
tripping a 401.

    GET /api/auth/me       → current user from the Bearer token (or authenticated:false)
    PUT /api/auth/country  → set the signed-in user's tax-residence country
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.auth import MeResponse, UpdateCountryRequest
from app.services import tax_summary
from app.services.auth import supabase_jwt
from app.services.auth import users as auth_users

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=MeResponse)
def me(request: Request, db: Session = Depends(get_db)) -> MeResponse:
    token = _bearer_token_from_request(request)
    claims = supabase_jwt.verify_access_token(token) if token else None
    if claims is None or not claims.email:
        return MeResponse(authenticated=False)

    user = auth_users.get_or_create_user_from_supabase(db, claims.user_id, claims.email)
    db.commit()
    return MeResponse(authenticated=True, email=user.email, country=user.country)


@router.put("/country", response_model=MeResponse)
def update_country(
    body: UpdateCountryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    """Set the signed-in user's tax-residence country (drives the tax summary + locale)."""
    code = body.country.strip().upper()
    if code not in tax_summary.COUNTRY_PROFILES:
        supported = ", ".join(sorted(tax_summary.COUNTRY_PROFILES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported country '{code}'. Supported: {supported}.",
        )
    user.country = code
    db.commit()
    return MeResponse(authenticated=True, email=user.email, country=user.country)
