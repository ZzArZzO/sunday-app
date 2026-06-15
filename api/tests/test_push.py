"""Push registration + send (dry-run) and weekly-briefing wiring.

Mirrors test_auth: functions are exercised directly against the in-memory `db`
fixture — no TestClient, no network. Without FCM credentials every send is a
dry-run, so the whole path is testable without a Firebase project.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import PushToken, User
from app.services.delivery import briefing_delivery, push_registry, push_sender


def _make_user(db, email="push@example.com") -> User:
    user = User(email=email)
    db.add(user)
    db.flush()
    return user


# --- registry ---------------------------------------------------------------


class TestRegisterToken:
    def test_creates_row(self, db):
        user = _make_user(db)
        row = push_registry.register_token(db, user, "tok-abc", "ios")
        assert row.id is not None
        assert row.user_id == user.id
        assert row.platform == "ios"
        assert db.query(PushToken).count() == 1

    def test_reregister_is_upsert_not_duplicate(self, db):
        user = _make_user(db)
        push_registry.register_token(db, user, "tok-abc", "android")
        push_registry.register_token(db, user, "tok-abc", "ios")
        rows = push_registry.tokens_for_user(db, user)
        assert len(rows) == 1
        assert rows[0].platform == "ios"  # platform updated in place

    def test_token_moves_to_new_owner(self, db):
        first = _make_user(db, "first@example.com")
        second = _make_user(db, "second@example.com")
        push_registry.register_token(db, first, "shared-tok", "android")
        push_registry.register_token(db, second, "shared-tok", "android")
        assert push_registry.tokens_for_user(db, first) == []
        assert len(push_registry.tokens_for_user(db, second)) == 1

    def test_unknown_platform_falls_back_to_android(self, db):
        user = _make_user(db)
        row = push_registry.register_token(db, user, "tok-x", "blackberry")
        assert row.platform == "android"

    def test_unregister(self, db):
        user = _make_user(db)
        push_registry.register_token(db, user, "tok-x", "android")
        assert push_registry.unregister_token(db, user, "tok-x") is True
        assert push_registry.tokens_for_user(db, user) == []
        assert push_registry.unregister_token(db, user, "tok-x") is False

    def test_unregister_is_scoped_to_owner(self, db):
        owner = _make_user(db, "owner@example.com")
        other = _make_user(db, "other@example.com")
        push_registry.register_token(db, owner, "owned-tok", "android")
        # A different user cannot delete (silence) someone else's device.
        assert push_registry.unregister_token(db, other, "owned-tok") is False
        assert len(push_registry.tokens_for_user(db, owner)) == 1

    def test_register_evicts_least_recently_seen_over_cap(self, db):
        from app.services.delivery.push_registry import MAX_TOKENS_PER_USER

        user = _make_user(db)
        base = datetime(2026, 6, 15, tzinfo=timezone.utc)
        for i in range(MAX_TOKENS_PER_USER + 3):
            push_registry.register_token(
                db, user, f"tok-{i}", "android", now=base + timedelta(seconds=i)
            )
        rows = push_registry.tokens_for_user(db, user)
        assert len(rows) == MAX_TOKENS_PER_USER
        # The earliest tokens (0, 1, 2) were evicted; the most recent survive.
        surviving = {r.token for r in rows}
        assert "tok-0" not in surviving
        assert f"tok-{MAX_TOKENS_PER_USER + 2}" in surviving


# --- sender (dry-run, no credentials) ---------------------------------------


class TestSendPushDryRun:
    def test_dry_run_without_credentials(self):
        res = push_sender.send_push("tok-abc", "Title", "Body", data={"k": "v"})
        assert res.ok is True
        assert res.dry_run is True
        assert res.error is None


# --- weekly-briefing wiring -------------------------------------------------


@dataclass(frozen=True)
class _FakeNetWorth:
    eur: Decimal


@dataclass(frozen=True)
class _FakeBriefing:
    net_worth: _FakeNetWorth
    week_of: str


class TestPushBriefing:
    def test_notifies_each_registered_device(self, db):
        user = _make_user(db)
        push_registry.register_token(db, user, "tok-1", "ios")
        push_registry.register_token(db, user, "tok-2", "android")
        briefing = _FakeBriefing(_FakeNetWorth(Decimal("24704.62")), "2026-06-15")

        sent = briefing_delivery._push_briefing(db, user, briefing)

        assert sent == 2  # both dry-run sends count as ok

    def test_no_devices_sends_nothing(self, db):
        user = _make_user(db)
        briefing = _FakeBriefing(_FakeNetWorth(Decimal("100.00")), "2026-06-15")
        assert briefing_delivery._push_briefing(db, user, briefing) == 0
