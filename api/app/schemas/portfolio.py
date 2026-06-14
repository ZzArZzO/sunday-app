from decimal import Decimal

from pydantic import BaseModel, Field


class DualMoney(BaseModel):
    """A monetary amount expressed in both EUR and USD, per the project's dual-currency convention."""

    eur: Decimal = Field(..., description="Amount in EUR")
    usd: Decimal = Field(..., description="Amount in USD at the report's FX rate")


class PositionView(BaseModel):
    id: int
    ticker: str
    isin: str | None = None
    asset_class: str
    sector: str | None = None
    region: str | None = None
    currency: str

    quantity: Decimal
    avg_cost_eur: Decimal
    last_price_eur: Decimal | None = None

    market_value: DualMoney
    cost_basis: DualMoney
    unrealised_pnl: DualMoney
    weight_pct: Decimal = Field(..., description="Share of portfolio market value, 0-100")


class ConcentrationItem(BaseModel):
    ticker: str
    weight_pct: Decimal
    threshold_pct: Decimal
    severity: str  # info | warning | alert


class PortfolioResponse(BaseModel):
    portfolio_id: int
    as_of: str
    # User's tax-residence country (ISO-3166 alpha-2) — drives locale formatting.
    country: str = "DE"
    fx_eur_usd: Decimal
    total_value: DualMoney
    total_cost: DualMoney
    total_pnl: DualMoney
    positions: list[PositionView]
    concentration: list[ConcentrationItem]
    asset_class_split: dict[str, Decimal]


class IngestResult(BaseModel):
    rows_read: int
    positions_created: int
    positions_updated: int
    lots_created: int
    warnings: list[str] = []
