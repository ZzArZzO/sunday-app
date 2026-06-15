"""Process Stripe webhook events — the source of truth for subscription state.

Signatures are always verified against the signing secret before any state change.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.billing import subscription
from app.services.billing.client import BillingNotConfigured, get_stripe

# Subscription lifecycle events that change a user's access tier.
_SUBSCRIPTION_EVENTS = frozenset(
    {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }
)


def _period_end(sub: dict) -> int | None:
    """Current period end (unix). Newer Stripe API versions moved this off the
    subscription object onto its line items, so fall back to the first item."""
    end = sub.get("current_period_end")
    if end:
        return end
    items = (sub.get("items") or {}).get("data") or []
    return items[0].get("current_period_end") if items else None


def process_event(db: Session, payload: bytes, sig_header: str | None) -> str:
    """Verify the signature and apply the event. Returns the handled event type.

    Raises stripe.error.SignatureVerificationError on a bad signature (the caller
    maps that to 400) and BillingNotConfigured when no signing secret is set.
    """
    secret = get_settings().stripe_webhook_secret
    if not secret:
        raise BillingNotConfigured("STRIPE_WEBHOOK_SECRET is not set.")

    stripe = get_stripe()
    event = stripe.Webhook.construct_event(payload, sig_header, secret)
    etype = event["type"]

    if etype in _SUBSCRIPTION_EVENTS:
        sub = event["data"]["object"]
        status = "canceled" if etype.endswith("deleted") else sub.get("status")
        subscription.apply_subscription(
            db,
            customer_id=sub["customer"],
            subscription_id=sub.get("id"),
            status=status,
            current_period_end=_period_end(sub),
        )

    return etype
