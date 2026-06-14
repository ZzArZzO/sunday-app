"""Tests for billing subscription state (services/billing/subscription).

Pure/DB-only — no Stripe network. Webhook signature handling and Checkout/Portal
session creation are thin wrappers over the Stripe SDK and are exercised against
a sandbox separately.
"""

from datetime import timezone

import pytest

from app.models import User
from app.services.billing import subscription


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
