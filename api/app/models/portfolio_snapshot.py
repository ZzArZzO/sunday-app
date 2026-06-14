from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PortfolioSnapshot(Base):
    """A point-in-time net-worth record. The history that makes week-over-week real.

    One row per portfolio per calendar day (upserted) — mirrors the seed's
    `portfolio-history.csv`. The briefing compares the live value to the most
    recent snapshot ~7 days old.
    """

    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "captured_on", name="uq_snapshot_portfolio_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )

    captured_on: Mapped[date] = mapped_column(Date)  # calendar day (one row/day)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # exact capture time

    total_value_eur: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_cost_eur: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    eur_usd_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    # {asset_class: eur_amount_as_string}; lets us do per-class WoW later.
    breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="snapshots")  # noqa: F821
