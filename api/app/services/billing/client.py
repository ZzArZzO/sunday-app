"""Stripe client factory.

Lazily configures the Stripe SDK from settings. Kept tiny and separate so tests
can monkeypatch without importing the SDK, and so the (restricted) key lives in
exactly one place. Never log the key.
"""

from __future__ import annotations

from types import ModuleType

import stripe

from app.config import get_settings


class BillingNotConfigured(RuntimeError):
    """Raised when a billing call is attempted without Stripe configured."""


def get_stripe() -> ModuleType:
    settings = get_settings()
    if not settings.stripe_api_key:
        raise BillingNotConfigured(
            "STRIPE_API_KEY is not set. Billing is unavailable until it is configured."
        )
    stripe.api_key = settings.stripe_api_key
    return stripe
