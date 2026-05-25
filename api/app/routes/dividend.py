from decimal import Decimal

from fastapi import APIRouter, Depends

from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas.dividend import DividendPositionView, DividendResponse
from app.services import dividend_projector, fx, pnl

router = APIRouter(prefix="/api/dividend", tags=["dividend"])


@router.get("", response_model=DividendResponse)
def get_dividend(portfolio: Portfolio = Depends(get_default_portfolio)) -> DividendResponse:
    quote = fx.get_eur_usd()
    positions = list(portfolio.positions)
    mv_by_id = {p.id: pnl.market_value_eur(p) for p in positions}

    lines = dividend_projector.project(positions, mv_by_id)
    total_annual = dividend_projector.total_annual_eur(lines)
    total_monthly = (total_annual / Decimal("12")).quantize(Decimal("0.01"))
    weighted = dividend_projector.weighted_yield_pct(lines)

    view_lines = [
        DividendPositionView(
            ticker=line.position.ticker,
            asset_class=line.position.asset_class,
            market_value=fx.dual(line.market_value_eur, quote.rate),
            yield_pct=line.yield_pct,
            annual_dividend=fx.dual(line.annual_dividend_eur, quote.rate),
            monthly_dividend=fx.dual(
                (line.annual_dividend_eur / Decimal("12")).quantize(Decimal("0.01")),
                quote.rate,
            ),
            source=line.source,
        )
        for line in lines
        if line.annual_dividend_eur > 0
    ]
    # Sort by annual dividend descending — biggest contributors first.
    view_lines.sort(key=lambda v: Decimal(v.annual_dividend.eur), reverse=True)

    notes = [
        "Dividend yields are indicative. Live distribution data lands in Phase 2.",
    ]
    if any(line.source == "estimate" for line in lines):
        notes.append("Positions without a known yield use an asset-class average.")

    return DividendResponse(
        total_annual=fx.dual(total_annual, quote.rate),
        total_monthly=fx.dual(total_monthly, quote.rate),
        weighted_yield_pct=weighted,
        forward_12m_growth_pct=dividend_projector.DEFAULT_DIVIDEND_GROWTH_PCT,
        positions=view_lines,
        notes=notes,
    )
