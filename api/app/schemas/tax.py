from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.portfolio import DualMoney


class TaxBracket(BaseModel):
    """One slice of a country's capital-gains tax model."""

    label: str
    rate_pct: Decimal
    applies_to: str = Field(..., description="Plain-English description of what this rate covers.")


class CryptoHoldingPeriodView(BaseModel):
    """One crypto lot's progress toward the tax-free holding mark. Informational."""

    ticker: str
    quantity: Decimal
    acquired_on: str  # YYYY-MM-DD
    days_held: int
    days_to_tax_free: int
    tax_free: bool


class TaxSummaryResponse(BaseModel):
    country: str = Field(..., description="ISO-3166 alpha-2")
    country_name: str
    base_rate_pct: Decimal = Field(..., description="Headline capital-gains rate for residents")
    annual_allowance_eur: Decimal = Field(..., description="Yearly tax-free gain allowance")
    brackets: list[TaxBracket]

    unrealised_gains: DualMoney
    estimated_tax_if_realised: DualMoney
    after_tax_value_if_realised: DualMoney

    annual_dividend_estimate: DualMoney
    estimated_dividend_tax: DualMoney

    # Crypto holding-period clock (DE/PT 365-day rule). Empty where not applicable.
    crypto_tax_free_after_days: int | None = None
    crypto_holding_periods: list[CryptoHoldingPeriodView] = Field(default_factory=list)

    notes: list[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "Information only — not tax advice. Real liability depends on your "
            "holding period, broker reporting, and personal circumstances."
        )
    )
