"""Customer Portal — self-service upgrade/downgrade/cancel/payment-method updates."""

from __future__ import annotations

from app.config import get_settings
from app.models import User
from app.services.billing.client import BillingNotConfigured, get_stripe


def create_portal_session(user: User) -> str:
    """Return a Stripe Customer Portal URL for managing the subscription."""
    if not user.stripe_customer_id:
        raise BillingNotConfigured("This user has no Stripe customer yet — subscribe first.")

    stripe = get_stripe()
    base = get_settings().app_base_url.rstrip("/")
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{base}/billing",
    )
    return session.url
