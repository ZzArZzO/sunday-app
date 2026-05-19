"""Seed a demo user + portfolio from the sample TR CSV.

Run with:
    python -m app.seeds.load_sample
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Portfolio, User
from app.services import csv_ingestor

SAMPLE_CSV = Path(__file__).parent / "sample-tr.csv"

# Demo price snapshot (EUR). Lets the dashboard show non-zero P&L without a
# live price fetcher. Replace in Phase 2.
DEMO_LAST_PRICES_EUR = {
    "VWCE": Decimal("112.40"),
    "SXR8": Decimal("510.20"),
    "ASML": Decimal("710.30"),
    "NESN": Decimal("88.40"),
    "BTC": Decimal("62000.00"),
    "ETH": Decimal("3200.00"),
    "SOL": Decimal("145.00"),
}


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == settings.demo_user_id))
        if user is None:
            user = User(
                id=settings.demo_user_id,
                email="demo@sunday.local",
                country="DE",
                timezone="Europe/Berlin",
            )
            db.add(user)
            db.flush()

        if not user.portfolios:
            portfolio = Portfolio(user_id=user.id, name="Main")
            db.add(portfolio)
            db.flush()
            user.portfolios.append(portfolio)
        else:
            portfolio = user.portfolios[0]
            portfolio.positions.clear()
            db.flush()

        raw = SAMPLE_CSV.read_text(encoding="utf-8")
        result = csv_ingestor.ingest_csv(db, portfolio, raw)

        for position in portfolio.positions:
            last = DEMO_LAST_PRICES_EUR.get(position.ticker)
            if last is not None:
                position.last_price_eur = last

        db.commit()
        print(
            f"Seeded user_id={user.id} portfolio_id={portfolio.id}: "
            f"{result.rows_read} rows, {result.positions_created} positions, "
            f"{result.lots_created} lots."
        )
        if result.warnings:
            print("Warnings:")
            for w in result.warnings:
                print(f"  - {w}")


if __name__ == "__main__":
    main()
