from decimal import Decimal

from fastapi import APIRouter, Depends

from app.deps import get_current_user, get_default_portfolio
from app.models import Portfolio, User
from app.schemas.fire import FireResponse, FireTimelinePoint
from app.services import fire_calculator, fx, pnl

router = APIRouter(prefix="/api/fire", tags=["fire"])


@router.get("", response_model=FireResponse)
def get_fire(
    portfolio: Portfolio = Depends(get_default_portfolio),
    user: User = Depends(get_current_user),
) -> FireResponse:
    quote = fx.get_eur_usd()

    total_value_eur = sum(
        (pnl.market_value_eur(p) for p in portfolio.positions), start=Decimal("0")
    )

    inputs = fire_calculator.FireInputs(
        current_net_worth_eur=total_value_eur,
        annual_expenses_eur=user.annual_expenses_eur,
        annual_savings_eur=user.annual_savings_eur,
        expected_real_return_pct=user.expected_real_return_pct,
        safe_withdrawal_rate_pct=user.safe_withdrawal_rate_pct,
        current_age=None,  # age is not yet captured on the User model
    )
    calc = fire_calculator.calculate(inputs)

    return FireResponse(
        annual_expenses_eur=user.annual_expenses_eur,
        annual_savings_eur=user.annual_savings_eur,
        expected_real_return_pct=user.expected_real_return_pct,
        safe_withdrawal_rate_pct=user.safe_withdrawal_rate_pct,
        current_net_worth=fx.dual(total_value_eur, quote.rate),
        full_fire_number=fx.dual(calc.full_fire_eur, quote.rate),
        coast_fire_number=fx.dual(calc.coast_fire_eur, quote.rate),
        lean_fire_number=fx.dual(calc.lean_fire_eur, quote.rate),
        fat_fire_number=fx.dual(calc.fat_fire_eur, quote.rate),
        full_fire_progress_pct=calc.full_fire_progress_pct,
        coast_fire_progress_pct=calc.coast_fire_progress_pct,
        years_to_full_fire=calc.years_to_full_fire,
        years_to_coast_fire=calc.years_to_coast_fire,
        timeline=[
            FireTimelinePoint(
                year_offset=p.year_offset,
                age=p.age,
                projected_net_worth_eur=p.projected_net_worth_eur,
                is_coast_fire=p.is_coast_fire,
                is_full_fire=p.is_full_fire,
            )
            for p in calc.timeline
        ],
        notes=calc.notes,
    )
