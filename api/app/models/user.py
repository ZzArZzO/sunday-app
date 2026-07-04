from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True already creates an index backing the constraint — index=True
    # would add a second, redundant one covering the same column.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    country: Mapped[str] = mapped_column(String(2), default="DE")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Berlin")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # FIRE planning inputs. Nullable so the UI can prompt for them.
    annual_expenses_eur: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    annual_savings_eur: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    expected_real_return_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("5.00")
    )
    safe_withdrawal_rate_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("4.00")
    )

    # Target allocation for rebalancing. Stored as JSON-ish via individual columns
    # to keep the schema flat. Sum should be 100 when set.
    target_etf_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("60.00"))
    target_stock_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("20.00"))
    target_crypto_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("15.00"))
    target_cash_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5.00"))

    # Delivery preferences. Opt-in is off by default — the weekly cron only emails
    # users who explicitly subscribe (no unsolicited briefings).
    weekly_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Billing (Stripe). Webhooks are the source of truth for these. ---
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    subscription_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    portfolios: Mapped[list["Portfolio"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
