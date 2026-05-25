"""FIRE planning schemas.

FIRE = Financial Independence, Retire Early. Numbers are derived deterministically
from user inputs (annual_expenses, savings, expected return) + current net worth.
All projections are nominal-EUR, real-return-adjusted per the user's settings.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.portfolio import DualMoney


class FireTimelinePoint(BaseModel):
    year_offset: int = Field(..., description="Years from now (0 = today)")
    age: int | None = Field(None, description="User's age that year, if known")
    projected_net_worth_eur: Decimal
    is_coast_fire: bool = Field(..., description="True once net worth crosses Coast FIRE number")
    is_full_fire: bool = Field(..., description="True once net worth crosses full FIRE number")


class FireResponse(BaseModel):
    # Inputs echoed back so the client can render context
    annual_expenses_eur: Decimal | None
    annual_savings_eur: Decimal | None
    expected_real_return_pct: Decimal
    safe_withdrawal_rate_pct: Decimal
    current_net_worth: DualMoney

    # Derived FIRE numbers
    full_fire_number: DualMoney = Field(
        ..., description="Annual expenses / safe withdrawal rate"
    )
    coast_fire_number: DualMoney = Field(
        ..., description="Today's nest egg that, untouched, grows into full FIRE by age 65"
    )
    lean_fire_number: DualMoney = Field(
        ..., description="Full FIRE × 0.6 — bare-essentials lifestyle"
    )
    fat_fire_number: DualMoney = Field(
        ..., description="Full FIRE × 2 — comfortable + buffer lifestyle"
    )

    # Progress
    full_fire_progress_pct: Decimal = Field(..., description="0–100+ ; can exceed 100")
    coast_fire_progress_pct: Decimal

    # Years to milestones (null if inputs incomplete or already reached)
    years_to_full_fire: Decimal | None
    years_to_coast_fire: Decimal | None

    # Year-by-year projection (up to 40 years)
    timeline: list[FireTimelinePoint]

    notes: list[str] = Field(
        default_factory=list,
        description="Caveats and computation notes (e.g. missing inputs).",
    )
