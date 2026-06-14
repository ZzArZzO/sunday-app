from datetime import datetime

from pydantic import BaseModel


class SubscriptionView(BaseModel):
    tier: str  # "free" | "pro"
    is_pro: bool
    status: str | None = None
    current_period_end: datetime | None = None


class CheckoutSessionView(BaseModel):
    url: str


class PortalSessionView(BaseModel):
    url: str
