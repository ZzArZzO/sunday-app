from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Lot(Base):
    """One purchase event. Multiple lots per position support FIFO P&L and DCA-tracking."""

    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="CASCADE"), index=True
    )

    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8))
    unit_cost_eur: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    fees_eur: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    source: Mapped[str] = mapped_column(String(32), default="manual")  # tr_csv | manual | dca

    # The import source this lot came from (null for legacy/pre-connection lots).
    # SET NULL on delete so disconnecting a source orphans rather than destroys
    # its lots; the service layer recomputes positions explicitly on re-sync.
    connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("connections.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    position: Mapped["Position"] = relationship(back_populates="lots")  # noqa: F821
    connection: Mapped["Connection | None"] = relationship(back_populates="lots")  # noqa: F821
