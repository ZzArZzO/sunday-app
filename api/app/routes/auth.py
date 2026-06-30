"""Magic-link authentication.

    POST /api/auth/request  {email}  → email a sign-in link (dry-run returns it)
    GET  /api/auth/verify?token=...  → consume token, set session cookie, redirect
    GET  /api/auth/me                → current session's user (or authenticated:false)
    POST /api/auth/logout            → revoke session + clear cookie

No-key behaviour: with no RESEND_API_KEY the email is a dry-run and the link is
returned in the response, so sign-in is testable end-to-end without a provider.
"""

from __future__ import annotations

import html as html_lib

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.rate_limit import rate_limit
from app.schemas.auth import (
    ExchangeRequest,
    ExchangeResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    MeResponse,
    UpdateCountryRequest,
)
from app.services import tax_summary
from app.services.auth import tokens as auth_tokens
from app.services.auth import users as auth_users
from app.services.delivery import sender

router = APIRouter(prefix="/api/auth", tags=["auth"])

_COOKIE_MAX_AGE = auth_tokens.SESSION_TTL_DAYS * 24 * 60 * 60


def _magic_email_html(link: str) -> str:
    safe = html_lib.escape(link)
    return (
        "<div style='font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#1a1a1a'>"
        "<p>Tap the button to sign in to <strong>Sunday</strong>:</p>"
        f"<p><a href='{safe}' style='display:inline-block;background:#1a1a1a;color:#fff;"
        "padding:10px 18px;border-radius:8px;text-decoration:none'>Sign in</a></p>"
        "<p style='color:#6b6b6b;font-size:13px'>This link expires in 15 minutes. "
        "If you didn't request it, you can ignore this email.</p></div>"
    )


@router.post(
    "/request",
    response_model=MagicLinkResponse,
    dependencies=[Depends(rate_limit("5/minute", "auth_request"))],
)
def request_magic_link(
    body: MagicLinkRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MagicLinkResponse:
    if not auth_users.is_valid_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email address."
        )

    user = auth_users.get_or_create_user(db, body.email)
    token = auth_tokens.create_magic_token(db, user)
    db.commit()

    link = f"{settings.api_base_url}/api/auth/verify?token={token}"
    result = sender.send_email(
        user.email, "Sign in to Sunday", _magic_email_html(link), f"Sign in to Sunday: {link}"
    )
    return MagicLinkResponse(
        sent=result.ok,
        dry_run=result.dry_run,
        dev_link=link if result.dry_run else None,
    )


@router.get("/verify", dependencies=[Depends(rate_limit("10/minute", "auth_verify"))])
def verify(
    token: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    user = auth_tokens.consume_magic_token(db, token)
    if user is None:
        return RedirectResponse(
            f"{settings.app_base_url}/signin?error=invalid_or_expired", status_code=303
        )
    session_token = auth_tokens.create_session(db, user)
    db.commit()

    response = RedirectResponse(settings.app_base_url, status_code=303)
    response.set_cookie(
        auth_tokens.SESSION_COOKIE,
        session_token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
    return response


@router.get("/me", response_model=MeResponse)
def me(request: Request, db: Session = Depends(get_db)) -> MeResponse:
    token = auth_tokens.session_token_from_request(request)
    user = auth_tokens.lookup_session(db, token) if token else None
    if user is None:
        return MeResponse(authenticated=False)
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


@router.post("/exchange", response_model=ExchangeResponse)
def exchange(body: ExchangeRequest, db: Session = Depends(get_db)) -> ExchangeResponse:
    """Mobile counterpart to GET /verify: trade a magic token for a session token
    as JSON (no cookie). The app stores it and sends it as `Authorization: Bearer`."""
    user = auth_tokens.consume_magic_token(db, body.magic_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired link."
        )
    session_token = auth_tokens.create_session(db, user)
    db.commit()
    return ExchangeResponse(
        session_token=session_token, email=user.email, country=user.country
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)) -> Response:
    token = auth_tokens.session_token_from_request(request)
    if token:
        auth_tokens.revoke_session(db, token)
        db.commit()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(auth_tokens.SESSION_COOKIE, path="/")
    return response
