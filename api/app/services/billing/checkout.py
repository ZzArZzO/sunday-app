"""Create Checkout Sessions (subscription) and ensure a Stripe customer per user."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User
from app.services.billing.client import BillingNotConfigured, get_stripe


def ensure_customer(db: Session, user: User) -> str:
    """Return the user's Stripe customer id, creating one on first use."""
    if user.stripe_customer_id:
        return user.stripe_customer_id

    stripe = get_stripe()
    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    db.add(user)
    db.commit()
    return customer.id


def create_checkout_session(db: Session, user: User) -> str:
    """Start a subscription Checkout Session for the Pro plan; return its URL."""
    settings = get_settings()
    if not settings.stripe_price_pro:
        raise BillingNotConfigured("STRIPE_PRICE_PRO is not set.")

    stripe = get_stripe()
    customer_id = ensure_customer(db, user)
    base = settings.app_base_url.rstrip("/")
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        # Do NOT pass payment_method_types — let Stripe pick eligible methods.
        line_items=[{"price": settings.stripe_price_pro, "quantity": 1}],
        # EU VAT: Stripe Tax computes tax; collect/confirm the customer's address.
        automatic_tax={"enabled": True},
        customer_update={"address": "auto", "name": "auto"},
        client_reference_id=str(user.id),
        success_url=f"{base}/billing?status=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base}/billing?status=cancel",
    )
    return session.url
