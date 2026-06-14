from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends

from app.deps import get_current_user, get_default_portfolio
from app.models import Portfolio, User
from app.schemas.tax import CryptoHoldingPeriodView, TaxBracket, TaxSummaryResponse
from app.services import dividend_projector, fx, pnl, tax_summary

router = APIRouter(prefix="/api/tax", tags=["tax"])


@router.get("", response_model=TaxSummaryResponse)
def get_tax_summary(
    portfolio: Portfolio = Depends(get_default_portfolio),
    user: User = Depends(get_current_user),
) -> TaxSummaryResponse:
    quote = fx.get_eur_usd()
    positions = list(portfolio.positions)

    total_value_eur = sum(
        (pnl.market_value_eur(p) for p in positions), start=Decimal("0")
    )
    total_cost_eur = sum(
        (pnl.cost_basis_eur(p) for p in positions), start=Decimal("0")
    )
    unrealised_gains = total_value_eur - total_cost_eur

    etf_value = sum(
        (pnl.market_value_eur(p) for p in positions if p.asset_class == "etf"),
        start=Decimal("0"),
    )
    etf_share_pct = (
        (etf_value / total_value_eur * Decimal("100")).quantize(Decimal("0.01"))
        if total_value_eur > 0
        else Decimal("0")
    )

    profile = tax_summary.profile_for(user.country)
    tax_calc = tax_summary.estimate_tax_on_unrealised(
        profile,
        unrealised_gains,
        total_value_eur,
        equity_etf_share_pct=etf_share_pct,
    )

    mv_by_id = {p.id: pnl.market_value_eur(p) for p in positions}
    div_lines = dividend_projector.project(positions, mv_by_id)
    annual_dividend = dividend_projector.total_annual_eur(div_lines)
    dividend_tax = tax_summary.estimate_dividend_tax(profile, annual_dividend)

    notes: list[str] = []
    if profile.code == "DE" and etf_share_pct > 0:
        notes.append(
            f"German Teilfreistellung applied: 30% of gains on the {etf_share_pct:.0f}% ETF "
            "portion are tax-exempt."
        )
    if profile.code == "NL":
        notes.append(
            "Netherlands uses a Box 3 wealth-tax model, not a realisation-based "
            "capital-gains model. The figure shown applies the deemed-return rate to your "
            "total holdings as a rough proxy."
        )
    if unrealised_gains <= 0:
        notes.append("No taxable gains today — portfolio is at or below cost basis.")

    # Crypto holding-period clock (DE/PT 365-day rule) — informational only.
    holding_views: list[CryptoHoldingPeriodView] = []
    if profile.crypto_tax_free_after_days is not None:
        periods = tax_summary.crypto_holding_periods(
            positions,
            now=datetime.now(timezone.utc),
            holding_period_days=profile.crypto_tax_free_after_days,
        )
        holding_views = [
            CryptoHoldingPeriodView(
                ticker=h.ticker,
                quantity=h.quantity,
                acquired_on=h.acquired_on.isoformat(),
                days_held=h.days_held,
                days_to_tax_free=h.days_to_tax_free,
                tax_free=h.tax_free,
            )
            for h in periods
        ]
        if holding_views:
            notes.append(
                f"In {profile.name}, privately-held crypto is generally tax-free after "
                f"{profile.crypto_tax_free_after_days} days. The dates below are informational, not advice."
            )

    return TaxSummaryResponse(
        country=profile.code,
        country_name=profile.name,
        base_rate_pct=profile.base_rate_pct,
        annual_allowance_eur=profile.annual_allowance_eur,
        brackets=[
            TaxBracket(label=b.label, rate_pct=b.rate_pct, applies_to=b.applies_to)
            for b in profile.brackets
        ],
        unrealised_gains=fx.dual(unrealised_gains, quote.rate),
        estimated_tax_if_realised=fx.dual(tax_calc.tax_due_eur, quote.rate),
        after_tax_value_if_realised=fx.dual(tax_calc.after_tax_value_eur, quote.rate),
        annual_dividend_estimate=fx.dual(annual_dividend, quote.rate),
        estimated_dividend_tax=fx.dual(dividend_tax, quote.rate),
        crypto_tax_free_after_days=profile.crypto_tax_free_after_days,
        crypto_holding_periods=holding_views,
        notes=notes,
    )
