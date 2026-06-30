"""Cache of ISIN → market-symbol resolutions.

Brokers like DEGIRO identify a holding only by ISIN (no ticker). To price it we
need the yfinance symbol (e.g. NL0010273215 → ASML.AS). Resolving via OpenFIGI is
a network call, so each result — including a miss (`symbol` NULL) — is cached
here so we never re-query the same ISIN. The curated `ISIN_TICKER_MAP` still
takes precedence; this table fills the long tail.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IsinSymbol(Base):
    __tablename__ = "isin_symbols"

    # ISIN is the natural key (12 chars), uppercased before write.
    isin: Mapped[str] = mapped_column(String(12), primary_key=True)
    # Resolved yfinance symbol, or NULL when the provider found no mapping
    # (cached so we don't keep asking for an unmappable ISIN).
    symbol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="openfigi")
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
