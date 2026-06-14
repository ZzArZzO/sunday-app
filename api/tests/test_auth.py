"""Tests for magic-link auth (services/auth). DB-backed via the in-memory fixture."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import MagicToken
from app.services.auth import tokens as auth_tokens
from app.services.auth import users as auth_users

NOW = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)


class TestGetOrCreateUser:
    def test_creates_user_and_default_portfolio_normalised(self, db: Session):
        user = auth_users.get_or_create_user(db, "  Marco@Example.COM ")
        assert user.email == "marco@example.com"
        assert len(list(user.portfolios)) == 1  # empty default portfolio

    def test_idempotent_by_email(self, db: Session):
        a = auth_users.get_or_create_user(db, "x@y.com")
        b = auth_users.get_or_create_user(db, "X@Y.com")
        assert a.id == b.id

    def test_email_validation(self):
        assert auth_users.is_valid_email("a@b.co")
        assert not auth_users.is_valid_email("nope")
        assert not auth_users.is_valid_email("a@b")


class TestMagicToken:
    def test_create_and_consume_once(self, db: Session):
        user = auth_users.get_or_create_user(db, "a@b.com")
        token = auth_tokens.create_magic_token(db, user, now=NOW)
        got = auth_tokens.consume_magic_token(db, token, now=NOW + timedelta(minutes=1))
        assert got is not None and got.id == user.id
        # single-use: a second consume fails.
        assert auth_tokens.consume_magic_token(db, token, now=NOW + timedelta(minutes=2)) is None

    def test_expired_token_rejected(self, db: Session):
        user = auth_users.get_or_create_user(db, "a@b.com")
        token = auth_tokens.create_magic_token(db, user, now=NOW)
        assert auth_tokens.consume_magic_token(db, token, now=NOW + timedelta(minutes=20)) is None

    def test_unknown_token_rejected(self, db: Session):
        assert auth_tokens.consume_magic_token(db, "garbage", now=NOW) is None

    def test_only_hash_is_stored(self, db: Session):
        user = auth_users.get_or_create_user(db, "a@b.com")
        token = auth_tokens.create_magic_token(db, user, now=NOW)
        row = db.query(MagicToken).first()
        assert row.token_hash != token and len(row.token_hash) == 64


class TestSession:
    def test_create_lookup_revoke(self, db: Session):
        user = auth_users.get_or_create_user(db, "a@b.com")
        token = auth_tokens.create_session(db, user, now=NOW)
        found = auth_tokens.lookup_session(db, token, now=NOW + timedelta(days=1))
        assert found is not None and found.id == user.id

        auth_tokens.revoke_session(db, token)
        assert auth_tokens.lookup_session(db, token, now=NOW + timedelta(days=1)) is None

    def test_expired_session_rejected(self, db: Session):
        user = auth_users.get_or_create_user(db, "a@b.com")
        token = auth_tokens.create_session(db, user, now=NOW)
        assert auth_tokens.lookup_session(db, token, now=NOW + timedelta(days=40)) is None

    def test_empty_token(self, db: Session):
        assert auth_tokens.lookup_session(db, "", now=NOW) is None


class _FakeReq:
    def __init__(self, headers: dict | None = None, cookies: dict | None = None):
        self.headers = headers or {}
        self.cookies = cookies or {}


class TestSessionTokenFromRequest:
    def test_bearer_header_wins(self):
        req = _FakeReq(
            headers={"Authorization": "Bearer abc123"},
            cookies={auth_tokens.SESSION_COOKIE: "cookieval"},
        )
        assert auth_tokens.session_token_from_request(req) == "abc123"

    def test_falls_back_to_cookie(self):
        req = _FakeReq(cookies={auth_tokens.SESSION_COOKIE: "cookieval"})
        assert auth_tokens.session_token_from_request(req) == "cookieval"

    def test_none_when_neither(self):
        assert auth_tokens.session_token_from_request(_FakeReq()) is None

    def test_ignores_non_bearer_scheme(self):
        req = _FakeReq(headers={"Authorization": "Basic xyz"})
        assert auth_tokens.session_token_from_request(req) is None

    def test_empty_bearer_is_ignored(self):
        req = _FakeReq(headers={"Authorization": "Bearer   "})
        assert auth_tokens.session_token_from_request(req) is None


class TestTokenAuthFlow:
    def test_exchange_returns_resolvable_session_token(self, db: Session):
        from app.routes.auth import exchange
        from app.schemas.auth import ExchangeRequest

        user = auth_users.get_or_create_user(db, "m@b.com")
        magic = auth_tokens.create_magic_token(db, user)
        db.commit()

        resp = exchange(ExchangeRequest(magic_token=magic), db)
        assert resp.session_token and resp.email == "m@b.com"
        # The returned token resolves to the same user.
        assert auth_tokens.lookup_session(db, resp.session_token).id == user.id

    def test_exchange_rejects_bad_magic_token(self, db: Session):
        from fastapi import HTTPException

        from app.routes.auth import exchange
        from app.schemas.auth import ExchangeRequest

        try:
            exchange(ExchangeRequest(magic_token="garbage"), db)
            raise AssertionError("expected HTTPException")
        except HTTPException as exc:
            assert exc.status_code == 401

    def test_get_current_user_resolves_bearer_token(self, db: Session):
        from app.config import get_settings
        from app.deps import get_current_user

        user = auth_users.get_or_create_user(db, "m@b.com")
        token = auth_tokens.create_session(db, user)
        db.commit()

        req = _FakeReq(headers={"Authorization": f"Bearer {token}"})
        got = get_current_user(req, db, get_settings())
        assert got.id == user.id
