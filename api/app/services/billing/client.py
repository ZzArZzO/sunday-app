"""Stripe client factory.

Lazily configures the Stripe SDK from settings. Kept tiny and separate so tests
can monkeypatch without importing the SDK, and so the (restricted) key lives in
exactly one place. Never log the key.
"""

from __future__ import annotations

import logging
from types import ModuleType

import stripe

from app.config import get_settings

log = logging.getLogger(__name__)


class BillingNotConfigured(RuntimeError):
    """Raised when a billing call is attempted without Stripe configured."""


def get_stripe() -> ModuleType:
    settings = get_settings()
    if not settings.stripe_api_key:
        raise BillingNotConfigured(
            "STRIPE_API_KEY is not set. Billing is unavailable until it is configured."
        )
    if not settings.stripe_api_key.startswith(("rk_live_", "rk_test_")):
        # Warn, don't fail — keeps an sk_test_ key working in dev, but flags the
        # least-privilege expectation for production. Never log the key itself.
        log.warning(
            "STRIPE_API_KEY does not look like a restricted key (rk_…). "
            "Use a restricted key in production."
        )
    stripe.api_key = settings.stripe_api_key
    return stripe
