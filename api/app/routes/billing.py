"""Billing endpoints — Stripe subscriptions for the Pro tier.

GET  /api/billing/subscription — current tier/status for the signed-in user
POST /api/billing/checkout     — start a Checkout Session, returns a redirect URL
POST /api/billing/portal       — open the Customer Portal, returns a redirect URL
POST /api/billing/webhook      — Stripe events (signature-verified, no auth)
"""

from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.billing import (
    AiBudgetView,
    CheckoutSessionView,
    LlmUsageSummary,
    PortalSessionView,
    SubscriptionView,
)
from app.services.billing import budget, checkout, portal, subscription, webhooks
from app.services.billing.client import BillingNotConfigured
from app.services.llm import cost_ledger

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/subscription", response_model=SubscriptionView)
def get_subscription(user: User = Depends(get_current_user)) -> SubscriptionView:
    return SubscriptionView(
        tier=subscription.tier_for(user),
        is_pro=subscription.is_pro(user),
        status=user.subscription_status,
        current_period_end=user.subscription_period_end,
    )


@router.post("/checkout", response_model=CheckoutSessionView)
def start_checkout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutSessionView:
    try:
        url = checkout.create_checkout_session(db, user)
    except BillingNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return CheckoutSessionView(url=url)


@router.post("/portal", response_model=PortalSessionView)
def open_portal(user: User = Depends(get_current_user)) -> PortalSessionView:
    try:
        url = portal.create_portal_session(user)
    except BillingNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return PortalSessionView(url=url)


@router.get("/ai-budget", response_model=AiBudgetView)
def ai_budget(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiBudgetView:
    """The signed-in user's monthly AI allowance: cap, spent month-to-date, remaining."""
    s = budget.status(db, user)
    return AiBudgetView(
        cap_usd=str(s["cap_usd"]),
        spent_usd=str(s["spent_usd"]),
        remaining_usd=str(s["remaining_usd"]),
        exhausted=s["exhausted"],
    )


@router.get("/llm-usage", response_model=LlmUsageSummary)
def llm_usage(
    days: int = 30,
    user: User = Depends(get_current_user),  # noqa: ARG001 - auth gate
    db: Session = Depends(get_db),
) -> LlmUsageSummary:
    """Measured AI COGS over the last `days`, total and per feature/user.

    TODO: gate behind an admin role before production — this exposes per-user
    cost aggregates. Auth-only for now.
    """
    return LlmUsageSummary(**cost_ledger.summary(db, days=days))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event_type = webhooks.process_event(db, payload, sig)
    except BillingNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except (stripe.error.SignatureVerificationError, ValueError):
        # Bad signature or unparseable payload — reject without leaking detail.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook")
    return {"received": True, "type": event_type}
