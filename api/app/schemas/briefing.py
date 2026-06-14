from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.portfolio import ConcentrationItem, DualMoney


class BriefingSection(BaseModel):
    """One section of the Sunday briefing. The frontend renders these in order."""

    kind: str = Field(
        ...,
        description="headline | what_changed | concentration | regime | tax_flags | movers",
    )
    title: str
    body_markdown: str
    data: dict | None = None


class BriefingResponse(BaseModel):
    portfolio_id: int
    week_of: str
    generated_at: str
    fx_eur_usd: Decimal
    net_worth: DualMoney
    wow_delta: DualMoney
    wow_delta_pct: Decimal
    # False until a prior week's snapshot exists — so the UI shows "building
    # history" rather than a misleading +0.00%.
    wow_available: bool = True
    wow_baseline_date: str | None = None
    sections: list[BriefingSection]
    concentration_alerts: list[ConcentrationItem]
    disclaimers: list[str] = Field(
        default_factory=lambda: [
            "Not investment advice. Information only.",
            "Generated with AI assistance.",
        ]
    )
