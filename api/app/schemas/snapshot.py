from decimal import Decimal

from pydantic import BaseModel

from app.schemas.portfolio import DualMoney


class SnapshotView(BaseModel):
    captured_on: str  # YYYY-MM-DD
    as_of: str
    total_value: DualMoney
    total_cost: DualMoney
    eur_usd_rate: Decimal


class SnapshotListResponse(BaseModel):
    count: int
    snapshots: list[SnapshotView]
