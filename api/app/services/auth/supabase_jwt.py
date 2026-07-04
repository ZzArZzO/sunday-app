"""Verifies Supabase Auth access tokens (JWTs) via JWKS.

Supabase's current direction is asymmetric JWT signing keys (ES256/RS256),
rotatable, published at the project's JWKS endpoint — no shared secret needed
on this side. `PyJWT`'s `PyJWKClient` handles fetching, caching, and picking
the right key by `kid` for us.

If a Supabase project is still on the legacy HS256 shared-secret path (older
projects), this module needs a different verification branch — check
Supabase dashboard → Authentication → JWT Keys before relying on this as-is.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Request
from jwt import PyJWKClient

from app.config import get_settings

log = logging.getLogger(__name__)

_ALGORITHMS = ["ES256", "RS256"]
_AUDIENCE = "authenticated"


@dataclass(frozen=True)
class SupabaseClaims:
    user_id: str  # auth.users.id (UUID as string)
    email: str | None
    aal: str  # Authenticator Assurance Level: "aal1" or "aal2"


def bearer_token_from_request(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if not header or not header.startswith("Bearer "):
        return None
    token = header[len("Bearer ") :].strip()
    return token or None


@lru_cache
def _jwks_client() -> PyJWKClient | None:
    supabase_url = get_settings().supabase_url
    if not supabase_url:
        return None
    return PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json")


def verify_access_token(token: str) -> SupabaseClaims | None:
    """Verify a Supabase access token. Returns None on any failure — callers
    decide what an invalid token means (401, or the demo-user fallback)."""
    client = _jwks_client()
    if client is None:
        return None

    settings = get_settings()
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=_ALGORITHMS,
            audience=_AUDIENCE,
            issuer=f"{settings.supabase_url}/auth/v1",
        )
    except jwt.PyJWTError as exc:
        log.info("Supabase JWT rejected: %s", exc)
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return SupabaseClaims(
        user_id=user_id,
        email=payload.get("email"),
        aal=payload.get("aal", "aal1"),
    )
