from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Connection(Base):
    """One import source attached to a portfolio.

    A portfolio aggregates N connections; each is a way data got in — a CSV
    upload, manual entry, an on-chain address, or a read-only exchange API key.
    Lots carry `connection_id` so a source's contribution can be re-synced or
    disconnected cleanly. Secrets are never stored here in plaintext (the
    `config` blob holds only non-secret data like a public address or exchange
    name; encrypted credentials live in their own column added with Phase 3).
    """

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )

    kind: Mapped[str] = mapped_column(String(16))  # manual | csv | address | exchange
    label: Mapped[str] = mapped_column(String(120))  # "Trade Republic", "0xabc…", "Kraken"
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | error | disconnected

    # Non-secret connector config: {"address": "0x…"} | {"exchange": "kraken"} | {"broker": "tr"}
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Fernet-encrypted credentials (exchange API key/secret). Never plaintext;
    # only set for exchange connections. See services/connectors/secrets.py.
    secret_enc: Mapped[str | None] = mapped_column(Text, nullable=True)

    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="connections")  # noqa: F821
    lots: Mapped[list["Lot"]] = relationship(back_populates="connection")  # noqa: F821
