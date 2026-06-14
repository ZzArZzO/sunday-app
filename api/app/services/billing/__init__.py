"""Stripe billing — subscriptions for the Pro tier.

Checkout Sessions (mode=subscription) + Customer Portal + signature-verified
webhooks as the source of truth for subscription state. Disabled gracefully when
STRIPE_API_KEY is unset (endpoints return 503), mirroring the LLM/email tiers.
"""

from app.services.billing.client import BillingNotConfigured, get_stripe

__all__ = ["BillingNotConfigured", "get_stripe"]
