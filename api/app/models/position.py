from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )

    # Not always a real market ticker: brokers without a clean symbol (Trade
    # Republic, DEGIRO) fall back to the human-readable instrument name, e.g.
    # "FTSE All-World High Dividend Yield USD (Dist)" (45 chars) — sized well
    # past the longest real-world fund name we've seen, not just a ticker.
    ticker: Mapped[str] = mapped_column(String(128), index=True)
    isin: Mapped[str | None] = mapped_column(String(12), nullable=True)
    asset_class: Mapped[str] = mapped_column(String(16))  # stock | etf | crypto | cash
    sector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8), default=Decimal("0"))
    avg_cost_eur: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    last_price_eur: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    last_price_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")  # noqa: F821
    lots: Mapped[list["Lot"]] = relationship(  # noqa: F821
        back_populates="position", cascade="all, delete-orphan"
    )
