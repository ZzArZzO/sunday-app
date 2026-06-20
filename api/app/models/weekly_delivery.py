"""Records that a user's weekly briefing was sent for a given ISO week.

The unique (user_id, iso_week) constraint is the idempotency guard for
`deliver_weekly`: a second scheduler run — or a second always-on instance —
cannot send the same user twice in the same week.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WeeklyDelivery(Base):
    __tablename__ = "weekly_deliveries"
    __table_args__ = (
        UniqueConstraint("user_id", "iso_week", name="uq_weekly_delivery_user_week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    iso_week: Mapped[str] = mapped_column(String(8))  # e.g. "2026-W25"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
