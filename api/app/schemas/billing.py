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


class LlmUsageFeature(BaseModel):
    feature: str
    calls: int
    cost_usd: str


class LlmUsageUser(BaseModel):
    user_id: int | None
    calls: int
    cost_usd: str


class LlmUsageSummary(BaseModel):
    days: int
    total_cost_usd: str
    total_calls: int
    by_feature: list[LlmUsageFeature]
    by_user: list[LlmUsageUser]


class AiBudgetView(BaseModel):
    cap_usd: str
    spent_usd: str
    remaining_usd: str
    exhausted: bool
