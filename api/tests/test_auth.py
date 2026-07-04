"""Tests for Supabase Auth JWT verification + user provisioning.

Signs test JWTs with a locally-generated RSA keypair and monkeypatches the
JWKS client to serve its public key, so verification runs for real (signature,
audience, issuer) without any network call to Supabase.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.orm import Session

from app.services.auth import supabase_jwt
from app.services.auth import users as auth_users

SUPABASE_URL = "https://project.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"
USER_ID = "11111111-1111-1111-1111-111111111111"

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


@dataclass
class _FakeSigningKey:
    key: object


class _FakeJWKClient:
    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        return _FakeSigningKey(key=_PUBLIC_KEY)


class _FakeSettings:
    supabase_url = SUPABASE_URL


@pytest.fixture()
def fake_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(supabase_jwt, "_jwks_client", lambda: _FakeJWKClient())
    monkeypatch.setattr(supabase_jwt, "get_settings", lambda: _FakeSettings())


def _token(sub: str = USER_ID, email: str | None = "a@b.com", aal: str = "aal1", **extra: str) -> str:
    payload = {"sub": sub, "email": email, "aal": aal, "aud": "authenticated", "iss": ISSUER, **extra}
    return jwt.encode(payload, _PRIVATE_KEY, algorithm="RS256")


class TestVerifyAccessToken:
    def test_valid_token_resolves_claims(self, fake_jwks: None) -> None:
        claims = supabase_jwt.verify_access_token(_token())
        assert claims is not None
        assert claims.user_id == USER_ID
        assert claims.email == "a@b.com"
        assert claims.aal == "aal1"

    def test_reads_mfa_assurance_level(self, fake_jwks: None) -> None:
        claims = supabase_jwt.verify_access_token(_token(aal="aal2"))
        assert claims is not None and claims.aal == "aal2"

    def test_wrong_audience_rejected(self, fake_jwks: None) -> None:
        assert supabase_jwt.verify_access_token(_token(aud="not-authenticated")) is None

    def test_wrong_issuer_rejected(self, fake_jwks: None) -> None:
        assert supabase_jwt.verify_access_token(_token(iss="https://evil.example/auth/v1")) is None

    def test_wrong_signing_key_rejected(self, fake_jwks: None) -> None:
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        payload = {"sub": USER_ID, "email": "a@b.com", "aal": "aal1", "aud": "authenticated", "iss": ISSUER}
        forged = jwt.encode(payload, other_key, algorithm="RS256")
        assert supabase_jwt.verify_access_token(forged) is None

    def test_garbage_token_rejected(self, fake_jwks: None) -> None:
        assert supabase_jwt.verify_access_token("not-a-jwt") is None

    def test_missing_supabase_url_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class _NoUrlSettings:
            supabase_url = ""

        monkeypatch.setattr(supabase_jwt, "get_settings", lambda: _NoUrlSettings())
        supabase_jwt._jwks_client.cache_clear()
        try:
            assert supabase_jwt.verify_access_token(_token()) is None
        finally:
            supabase_jwt._jwks_client.cache_clear()


class TestBearerTokenFromRequest:
    class _FakeReq:
        def __init__(self, headers: dict | None = None):
            self.headers = headers or {}

    def test_bearer_header_extracted(self) -> None:
        req = self._FakeReq(headers={"Authorization": "Bearer abc123"})
        assert supabase_jwt.bearer_token_from_request(req) == "abc123"

    def test_none_when_missing(self) -> None:
        assert supabase_jwt.bearer_token_from_request(self._FakeReq()) is None

    def test_ignores_non_bearer_scheme(self) -> None:
        req = self._FakeReq(headers={"Authorization": "Basic xyz"})
        assert supabase_jwt.bearer_token_from_request(req) is None

    def test_empty_bearer_is_ignored(self) -> None:
        req = self._FakeReq(headers={"Authorization": "Bearer   "})
        assert supabase_jwt.bearer_token_from_request(req) is None


class TestGetOrCreateUserFromSupabase:
    def test_creates_user_and_default_portfolio(self, db: Session) -> None:
        user = auth_users.get_or_create_user_from_supabase(db, USER_ID, "Marco@Example.COM")
        assert user.supabase_user_id == USER_ID
        assert user.email == "marco@example.com"
        assert len(list(user.portfolios)) == 1

    def test_idempotent_by_supabase_user_id(self, db: Session) -> None:
        a = auth_users.get_or_create_user_from_supabase(db, USER_ID, "a@b.com")
        b = auth_users.get_or_create_user_from_supabase(db, USER_ID, "a@b.com")
        assert a.id == b.id

    def test_bridges_existing_row_by_email(self, db: Session) -> None:
        # A row that predates Supabase (e.g. seeded directly) has no supabase_user_id yet.
        from app.models import Portfolio, User

        existing = User(email="preexisting@b.com")
        db.add(existing)
        db.flush()
        db.add(Portfolio(user_id=existing.id, name="Main"))
        db.flush()

        bridged = auth_users.get_or_create_user_from_supabase(db, USER_ID, "PreExisting@b.com")
        assert bridged.id == existing.id
        assert bridged.supabase_user_id == USER_ID


class TestGetCurrentUser:
    class _FakeReq:
        def __init__(self, headers: dict | None = None):
            self.headers = headers or {}

    class _FakeSettings:
        def __init__(self, auth_required: bool = True, demo_user_id: int = 1):
            self.auth_required = auth_required
            self.demo_user_id = demo_user_id

    def test_resolves_user_from_valid_bearer_token(self, db: Session, fake_jwks: None) -> None:
        from app.deps import get_current_user

        req = self._FakeReq(headers={"Authorization": f"Bearer {_token()}"})
        user = get_current_user(req, db, self._FakeSettings())
        assert user.supabase_user_id == USER_ID
        assert user.email == "a@b.com"

    def test_no_token_and_auth_required_raises_401(self, db: Session) -> None:
        from fastapi import HTTPException

        from app.deps import get_current_user

        with pytest.raises(HTTPException) as exc:
            get_current_user(self._FakeReq(), db, self._FakeSettings(auth_required=True))
        assert exc.value.status_code == 401

    def test_no_token_and_auth_not_required_falls_back_to_demo_user(self, db: Session) -> None:
        from app.deps import get_current_user
        from app.models import User

        demo = User(email="demo@example.com")
        db.add(demo)
        db.flush()

        got = get_current_user(self._FakeReq(), db, self._FakeSettings(auth_required=False, demo_user_id=demo.id))
        assert got.id == demo.id

    def test_invalid_token_and_auth_required_raises_401(self, db: Session, fake_jwks: None) -> None:
        from fastapi import HTTPException

        from app.deps import get_current_user

        req = self._FakeReq(headers={"Authorization": "Bearer garbage"})
        with pytest.raises(HTTPException) as exc:
            get_current_user(req, db, self._FakeSettings(auth_required=True))
        assert exc.value.status_code == 401
