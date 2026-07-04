"""Live price refresh endpoint.

POST /api/prices/refresh — fetch live prices for the default portfolio's
holdings, convert to EUR, and persist `last_price_eur`. Also refreshes EUR/USD.

Sync handler (like the rest of the app); FastAPI runs it in a threadpool, so the
blocking network calls don't stall the event loop.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas.prices import PriceRefreshResponse
from app.services import fx, snapshots
from app.services.prices import isin_resolver
from app.services.prices import refresh as prices_refresh
from app.services.prices.base import PricesUnavailable
from app.services.prices.yfinance_provider import YFinanceProvider

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.post("/refresh", response_model=PriceRefreshResponse)
def refresh_prices(
    db: Session = Depends(get_db),
    portfolio: Portfolio = Depends(get_default_portfolio),
) -> PriceRefreshResponse:
    provider = YFinanceProvider()
    now = datetime.now(timezone.utc)

    try:
        eur_usd = prices_refresh.refresh_eur_usd(provider)
    except PricesUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    if eur_usd is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch the EUR/USD rate from the price provider.",
        )

    cross_rates = prices_refresh.fetch_cross_rates(provider)

    # Resolve ISIN-only holdings (e.g. DEGIRO) to market symbols so they price.
    positions = list(portfolio.positions)
    isin_map = isin_resolver.resolve(db, [p.isin for p in positions if p.isin])

    result = prices_refresh.price_positions(
        positions,
        provider,
        eur_usd_rate=eur_usd,
        cross_rates=cross_rates,
        isin_map=isin_map,
        now=now,
    )
    db.commit()

    # Record today's net worth now that prices are fresh, so week-over-week
    # history accumulates as a side effect of normal use (upsert by day).
    snapshots.capture(db, portfolio, now=now)
    db.commit()

    quote = fx.get_eur_usd()
    return PriceRefreshResponse(
        priced=result.priced,
        unpriced=result.unpriced,
        total=result.total,
        eur_usd_rate=quote.rate,
        eur_usd_source=quote.source,
        refreshed_at=now.isoformat(),
        warnings=result.warnings,
    )
