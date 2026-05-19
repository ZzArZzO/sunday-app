from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends

from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas import PortfolioResponse, PositionView
from app.services import concentration, fx, pnl

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
def get_portfolio(portfolio: Portfolio = Depends(get_default_portfolio)) -> PortfolioResponse:
    quote = fx.get_eur_usd()
    positions = list(portfolio.positions)

    total_value_eur = sum((pnl.market_value_eur(p) for p in positions), start=Decimal("0"))
    total_cost_eur = sum((pnl.cost_basis_eur(p) for p in positions), start=Decimal("0"))
    total_pnl_eur = total_value_eur - total_cost_eur

    weighted = concentration.position_weights(positions, total_value_eur)

    position_views = [
        PositionView(
            id=p.id,
            ticker=p.ticker,
            isin=p.isin,
            asset_class=p.asset_class,
            sector=p.sector,
            region=p.region,
            currency=p.currency,
            quantity=p.quantity,
            avg_cost_eur=p.avg_cost_eur,
            last_price_eur=p.last_price_eur,
            market_value=fx.dual(pnl.market_value_eur(p), quote.rate),
            cost_basis=fx.dual(pnl.cost_basis_eur(p), quote.rate),
            unrealised_pnl=fx.dual(pnl.unrealised_pnl_eur(p), quote.rate),
            weight_pct=weight,
        )
        for p, weight in weighted
    ]

    return PortfolioResponse(
        portfolio_id=portfolio.id,
        as_of=datetime.now(timezone.utc).isoformat(),
        fx_eur_usd=quote.rate,
        total_value=fx.dual(total_value_eur, quote.rate),
        total_cost=fx.dual(total_cost_eur, quote.rate),
        total_pnl=fx.dual(total_pnl_eur, quote.rate),
        positions=position_views,
        concentration=concentration.detect_concentration(positions, total_value_eur),
        asset_class_split=concentration.asset_class_split(positions, total_value_eur),
    )
