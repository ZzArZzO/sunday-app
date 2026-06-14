"""Tests for billing subscription state (services/billing/subscription).

Pure/DB-only — no Stripe network. Webhook signature handling and Checkout/Portal
session creation are thin wrappers over the Stripe SDK and are exercised against
a sandbox separately.
"""

import hashlib
import hmac
import json
import time
from datetime import timezone

import pytest
import stripe

from app.config import get_settings
from app.models import User
from app.services.billing import subscription, webhooks


def _signed_header(payload: bytes, secret: str) -> str:
    """Build a valid Stripe-Signature header: t=<ts>,v1=HMAC-SHA256(secret, "ts.payload")."""
    ts = int(time.time())
    prefix = f"{ts}.".encode()
    sig = hmac.new(secret.encode(), prefix + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


class TestTier:
    @pytest.mark.parametrize("status", ["active", "trialing"])
    def test_pro_statuses_grant_pro(self, status):
        user = User(email="a@test.com", subscription_status=status)
        assert subscription.is_pro(user) is True
        assert subscription.tier_for(user) == "pro"

    @pytest.mark.parametrize("status", [None, "canceled", "past_due", "incomplete", "unpaid"])
    def test_non_pro_statuses_are_free(self, status):
        user = User(email="a@test.com", subscription_status=status)
        assert subscription.is_pro(user) is False
        assert subscription.tier_for(user) == "free"

    def test_holdings_limit_caps_free_and_unlimits_pro(self):
        free = User(email="a@test.com")
        pro = User(email="b@test.com", subscription_status="active")
        assert subscription.holdings_limit(free) == subscription.FREE_HOLDINGS_CAP
        assert subscription.holdings_limit(pro) is None


class TestApplySubscription:
    def test_applies_state_to_matching_customer(self, db):
        user = User(email="sub@test.com", stripe_customer_id="cus_123")
        db.add(user)
        db.commit()

        updated = subscription.apply_subscription(
            db,
            customer_id="cus_123",
            subscription_id="sub_abc",
            status="active",
            current_period_end=1_800_000_000,
        )

        assert updated is not None
        assert updated.subscription_status == "active"
        assert updated.stripe_subscription_id == "sub_abc"
        # SQLite returns naive UTC, Postgres returns aware — compare the instant.
        end = updated.subscription_period_end
        assert end is not None
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        assert int(end.timestamp()) == 1_800_000_000
        assert subscription.is_pro(updated) is True

    def test_cancellation_drops_to_free(self, db):
        user = User(
            email="sub@test.com",
            stripe_customer_id="cus_123",
            subscription_status="active",
        )
        db.add(user)
        db.commit()

        subscription.apply_subscription(
            db,
            customer_id="cus_123",
            subscription_id="sub_abc",
            status="canceled",
            current_period_end=None,
        )

        assert subscription.tier_for(user) == "free"
        assert user.subscription_period_end is None

    def test_unknown_customer_is_ignored(self, db):
        result = subscription.apply_subscription(
            db,
            customer_id="cus_does_not_exist",
            subscription_id="sub_x",
            status="active",
            current_period_end=None,
        )
        assert result is None


class TestWebhook:
    def _configure(self, monkeypatch) -> str:
        settings = get_settings()
        monkeypatch.setattr(settings, "stripe_api_key", "sk_test_dummy")
        monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test_secret")
        return "whsec_test_secret"

    def test_verified_subscription_event_upgrades_user(self, db, monkeypatch):
        secret = self._configure(monkeypatch)
        user = User(email="w@test.com", stripe_customer_id="cus_x")
        db.add(user)
        db.commit()

        event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_1",
                    "customer": "cus_x",
                    "status": "active",
                    "current_period_end": 1_800_000_000,
                }
            },
        }
        payload = json.dumps(event).encode()

        etype = webhooks.process_event(db, payload, _signed_header(payload, secret))

        assert etype == "customer.subscription.created"
        assert user.subscription_status == "active"
        assert subscription.is_pro(user) is True

    def test_subscription_deleted_downgrades_user(self, db, monkeypatch):
        secret = self._configure(monkeypatch)
        user = User(
            email="w@test.com", stripe_customer_id="cus_x", subscription_status="active"
        )
        db.add(user)
        db.commit()

        event = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_1", "customer": "cus_x", "status": "canceled"}},
        }
        payload = json.dumps(event).encode()

        webhooks.process_event(db, payload, _signed_header(payload, secret))

        assert user.subscription_status == "canceled"
        assert subscription.is_pro(user) is False

    def test_bad_signature_is_rejected(self, db, monkeypatch):
        self._configure(monkeypatch)
        payload = b'{"type":"customer.subscription.created","data":{"object":{}}}'
        with pytest.raises(stripe.error.SignatureVerificationError):
            webhooks.process_event(db, payload, "t=1,v1=deadbeef")
