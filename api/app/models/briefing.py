from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Briefing(Base):
    """A generated Sunday briefing snapshot. Persisted so the user can revisit prior weeks."""

    __tablename__ = "briefings"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )
    week_of: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD (Sunday)
    payload: Mapped[dict] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
