from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.portfolio import DualMoney


class RebalanceLeg(BaseModel):
    asset_class: str
    current_pct: Decimal
    target_pct: Decimal
    drift_pct: Decimal = Field(..., description="current_pct - target_pct; positive = overweight")
    current_value: DualMoney
    target_value: DualMoney
    delta: DualMoney = Field(..., description="Positive = buy more; negative = sell")
    action: str = Field(..., description="buy | sell | hold")


class RebalanceResponse(BaseModel):
    total_value: DualMoney
    drift_score: Decimal = Field(
        ...,
        description="Sum of absolute drifts. 0 = perfectly aligned; 100+ = severe drift.",
    )
    needs_rebalance: bool = Field(
        ..., description="True if drift_score crosses the 5% rule-of-thumb threshold."
    )
    legs: list[RebalanceLeg]
    method: str = Field(
        ...,
        description="threshold | proportional — the method used to produce the suggestion.",
    )
    notes: list[str] = Field(default_factory=list)
