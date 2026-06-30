from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), default="Main")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="portfolios")  # noqa: F821
    positions: Mapped[list["Position"]] = relationship(  # noqa: F821
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["PortfolioSnapshot"]] = relationship(  # noqa: F821
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="PortfolioSnapshot.as_of",
    )
    connections: Mapped[list["Connection"]] = relationship(  # noqa: F821
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
