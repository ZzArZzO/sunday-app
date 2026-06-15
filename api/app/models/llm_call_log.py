from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class LlmCallLog(Base):
    """One row per Anthropic API call — the per-user AI cost ledger.

    Lets us read true per-user COGS from live traffic instead of estimating.
    `user_id` is null for shared calls (e.g. the weekly market layer, billed once
    for everyone). `cost_usd` is computed at write time from the model + token
    counts, so historical rows stay correct even if prices change later.
    """

    __tablename__ = "llm_call_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    feature: Mapped[str] = mapped_column(String(32))  # chat | briefing_narrative | market_layer | ...
    model: Mapped[str] = mapped_column(String(48))
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    portfolio_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)

    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))
