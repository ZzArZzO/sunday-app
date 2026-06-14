from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.portfolio import DualMoney


class BenchmarkPoint(BaseModel):
    on: str  # YYYY-MM-DD
    portfolio_twr_pct: Decimal
    index_twr_pct: Decimal | None = None


class BenchmarkResponse(BaseModel):
    available: bool
    index_key: str
    index_name: str
    index_available: bool
    series: list[BenchmarkPoint] = Field(default_factory=list)
    portfolio_pct: Decimal | None = None
    index_pct: Decimal | None = None
    diff_pct: Decimal | None = None
    diff: DualMoney | None = None  # € (and USD) impact of the performance gap
    note: str | None = None
    disclaimer: str = Field(
        default=(
            "Approximate time-weighted return from your snapshot history, shown for "
            "orientation only — not advice, and not a verdict on your decisions."
        )
    )
