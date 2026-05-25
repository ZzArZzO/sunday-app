from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.portfolio import DualMoney


class DividendPositionView(BaseModel):
    ticker: str
    asset_class: str
    market_value: DualMoney
    yield_pct: Decimal = Field(..., description="Annual yield estimate, 0-100")
    annual_dividend: DualMoney
    monthly_dividend: DualMoney
    source: str = Field(..., description="estimate | known")


class DividendResponse(BaseModel):
    total_annual: DualMoney
    total_monthly: DualMoney
    weighted_yield_pct: Decimal
    forward_12m_growth_pct: Decimal = Field(
        ..., description="Assumed dividend growth over the next 12 months."
    )
    positions: list[DividendPositionView]
    notes: list[str] = Field(default_factory=list)
