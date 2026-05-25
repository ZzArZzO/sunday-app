"""Briefing composer (deterministic, no LLM).

Phase 2 will introduce a Claude narrative wrapper:
    - Sonnet 4.6 shared market layer (cached across users, weekly batch)
    - Haiku 4.5 per-user narrative consuming the cached shared layer
    - `narrative-guardrails` post-generation filter for MiFID II compliance

The composer's contract stays the same: take a portfolio snapshot + market
context, return a structured BriefingResponse. The narrative wrapper only fills
in body_markdown fields; numbers always come from this deterministic layer.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from app.models import Portfolio
from app.schemas import BriefingResponse, BriefingSection, ConcentrationItem
from app.services import (
    concentration,
    dividend_projector,
    fire_calculator,
    fx,
    pnl,
    rebalancer,
    tax_summary,
)


def _format_eur(amount: Decimal) -> str:
    return f"€{amount:,.2f}"


def _format_pct(pct: Decimal) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _build_headline(net_worth_eur: Decimal, wow_delta_eur: Decimal, wow_pct: Decimal) -> BriefingSection:
    body = (
        f"Net worth: **{_format_eur(net_worth_eur)}**.\n\n"
        f"Week over week: **{_format_pct(wow_pct)}** "
        f"({_format_eur(wow_delta_eur)})."
    )
    return BriefingSection(kind="headline", title="The number that matters", body_markdown=body)


def _build_concentration_section(items: list[ConcentrationItem]) -> BriefingSection:
    if not items:
        body = "No positions cross your concentration thresholds this week."
    else:
        lines = [
            f"- **{i.ticker}** — {i.weight_pct:.2f}% "
            f"(your {i.severity} threshold is {i.threshold_pct:.2f}%)"
            for i in items
        ]
        body = "Positions that crossed your configured thresholds:\n\n" + "\n".join(lines)
    return BriefingSection(
        kind="concentration",
        title="Concentration",
        body_markdown=body,
        data={"items": [i.model_dump(mode="json") for i in items]},
    )


def _build_regime_section() -> BriefingSection:
    body = (
        "Regime detection is not active in this preview. "
        "The full briefing will include a risk-on/risk-off tag, cycle position, "
        "sector rotation snapshot, and a crypto-cycle indicator — all informational."
    )
    return BriefingSection(kind="regime", title="Market regime", body_markdown=body)


def _build_what_changed_placeholder() -> BriefingSection:
    body = (
        "Curated weekly items will appear here once the shared market layer is wired in. "
        "Expect 3–5 observations: earnings for held names, macro shifts you care about, "
        "and positions that moved meaningfully."
    )
    return BriefingSection(
        kind="what_changed", title="What changed this week", body_markdown=body
    )


def _build_fire_section(calc: fire_calculator.FireCalculation) -> BriefingSection:
    progress = calc.full_fire_progress_pct
    years = calc.years_to_full_fire
    when = f"{years:.1f} years" if years is not None else "not enough info"
    body = (
        f"You're at **{progress:.1f}%** of full FIRE "
        f"({_format_eur(calc.full_fire_eur)}).\n\n"
        f"At your current pace: **{when}** to financial independence.\n\n"
        f"Coast FIRE number (no further saving needed): {_format_eur(calc.coast_fire_eur)}."
    )
    return BriefingSection(
        kind="fire",
        title="Financial independence",
        body_markdown=body,
        data={
            "full_fire_progress_pct": float(progress),
            "years_to_full_fire": float(years) if years is not None else None,
        },
    )


def _build_dividend_section(
    lines: list[dividend_projector.DividendLine],
    annual_eur: Decimal,
) -> BriefingSection:
    monthly = (annual_eur / Decimal("12")).quantize(Decimal("0.01"))
    top = sorted(lines, key=lambda line: line.annual_dividend_eur, reverse=True)[:3]
    top_lines = "\n".join(
        f"- **{line.position.ticker}** — {_format_eur(line.annual_dividend_eur)} / yr "
        f"({line.yield_pct:.2f}% yield)"
        for line in top
        if line.annual_dividend_eur > 0
    )
    body = (
        f"Forward 12-month income: **{_format_eur(annual_eur)}** "
        f"(~{_format_eur(monthly)}/month).\n\n"
        f"Top contributors:\n\n{top_lines or '_No dividend-paying positions detected._'}"
    )
    return BriefingSection(kind="dividend", title="Dividend income", body_markdown=body)


def _build_tax_section(profile: tax_summary.CountryTaxProfile, tax_due_eur: Decimal) -> BriefingSection:
    body = (
        f"Estimated tax if you realised all unrealised gains today "
        f"({profile.name}, {profile.base_rate_pct}% headline): "
        f"**{_format_eur(tax_due_eur)}**.\n\n"
        f"Annual tax-free allowance: {_format_eur(profile.annual_allowance_eur)}.\n\n"
        f"_Information only — not tax advice._"
    )
    return BriefingSection(kind="tax_flags", title="Tax flags", body_markdown=body)


def _build_rebalance_section(calc: rebalancer.RebalanceCalc) -> BriefingSection:
    if not calc.needs_rebalance:
        body = (
            f"No leg drifts more than {rebalancer.DRIFT_TRIGGER_PCT}% from target — "
            "the portfolio is broadly in balance."
        )
    else:
        movers = [leg for leg in calc.legs if leg.action != "hold"]
        lines = "\n".join(
            f"- **{leg.asset_class}** — {leg.current_pct:.1f}% → {leg.target_pct:.1f}% "
            f"({leg.action} {_format_eur(abs(leg.delta_eur))})"
            for leg in movers
        )
        body = f"Drift score: **{calc.drift_score:.1f}**. Suggested adjustments:\n\n{lines}"
    return BriefingSection(kind="rebalance", title="Rebalance check", body_markdown=body)


def compose_briefing(portfolio: Portfolio) -> BriefingResponse:
    quote = fx.get_eur_usd()
    positions = list(portfolio.positions)
    user = portfolio.user

    total_value_eur = sum(
        (pnl.market_value_eur(p) for p in positions), start=Decimal("0")
    )
    total_cost_eur = sum(
        (pnl.cost_basis_eur(p) for p in positions), start=Decimal("0")
    )

    wow_delta_eur = Decimal("0")
    wow_pct = Decimal("0")

    items = concentration.detect_concentration(positions, total_value_eur)

    fire_calc = fire_calculator.calculate(
        fire_calculator.FireInputs(
            current_net_worth_eur=total_value_eur,
            annual_expenses_eur=user.annual_expenses_eur if user else None,
            annual_savings_eur=user.annual_savings_eur if user else None,
            expected_real_return_pct=(
                user.expected_real_return_pct if user else Decimal("5.00")
            ),
            safe_withdrawal_rate_pct=(
                user.safe_withdrawal_rate_pct if user else Decimal("4.00")
            ),
        )
    )

    mv_by_id = {p.id: pnl.market_value_eur(p) for p in positions}
    div_lines = dividend_projector.project(positions, mv_by_id)
    annual_div = dividend_projector.total_annual_eur(div_lines)

    country_code = user.country if user else "DE"
    tax_profile = tax_summary.profile_for(country_code)
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
    tax_calc = tax_summary.estimate_tax_on_unrealised(
        tax_profile,
        unrealised_gains,
        total_value_eur,
        equity_etf_share_pct=etf_share_pct,
    )

    rebal_calc = (
        rebalancer.suggest(positions, user)
        if user is not None
        else rebalancer.RebalanceCalc(
            total_value_eur=Decimal("0"),
            drift_score=Decimal("0"),
            needs_rebalance=False,
            legs=[],
            notes=["No user profile."],
        )
    )

    sections: list[BriefingSection] = [
        _build_headline(total_value_eur, wow_delta_eur, wow_pct),
        _build_what_changed_placeholder(),
        _build_fire_section(fire_calc),
        _build_concentration_section(items),
        _build_rebalance_section(rebal_calc),
        _build_dividend_section(div_lines, annual_div),
        _build_tax_section(tax_profile, tax_calc.tax_due_eur),
        _build_regime_section(),
    ]

    today = date.today().isoformat()

    return BriefingResponse(
        portfolio_id=portfolio.id,
        week_of=today,
        generated_at=datetime.now(timezone.utc).isoformat(),
        fx_eur_usd=quote.rate,
        net_worth=fx.dual(total_value_eur, quote.rate),
        wow_delta=fx.dual(wow_delta_eur, quote.rate),
        wow_delta_pct=wow_pct,
        sections=sections,
        concentration_alerts=items,
    )
