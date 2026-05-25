from fastapi import APIRouter, Depends

from app.deps import get_current_user, get_default_portfolio
from app.models import Portfolio, User
from app.schemas.rebalance import RebalanceLeg, RebalanceResponse
from app.services import fx, rebalancer

router = APIRouter(prefix="/api/rebalance", tags=["rebalance"])


@router.get("", response_model=RebalanceResponse)
def get_rebalance(
    portfolio: Portfolio = Depends(get_default_portfolio),
    user: User = Depends(get_current_user),
) -> RebalanceResponse:
    quote = fx.get_eur_usd()
    calc = rebalancer.suggest(list(portfolio.positions), user)

    legs = [
        RebalanceLeg(
            asset_class=leg.asset_class,
            current_pct=leg.current_pct,
            target_pct=leg.target_pct,
            drift_pct=leg.current_pct - leg.target_pct,
            current_value=fx.dual(leg.current_value_eur, quote.rate),
            target_value=fx.dual(leg.target_value_eur, quote.rate),
            delta=fx.dual(leg.delta_eur, quote.rate),
            action=leg.action,
        )
        for leg in calc.legs
    ]

    return RebalanceResponse(
        total_value=fx.dual(calc.total_value_eur, quote.rate),
        drift_score=calc.drift_score,
        needs_rebalance=calc.needs_rebalance,
        legs=legs,
        method="threshold",
        notes=calc.notes,
    )
