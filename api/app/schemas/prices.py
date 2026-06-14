from decimal import Decimal

from pydantic import BaseModel


class PriceRefreshResponse(BaseModel):
    priced: int
    unpriced: int
    total: int
    eur_usd_rate: Decimal
    eur_usd_source: str
    refreshed_at: str
    warnings: list[str]
