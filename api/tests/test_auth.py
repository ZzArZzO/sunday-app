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
