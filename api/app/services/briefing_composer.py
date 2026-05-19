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
from app.services import concentration, fx, pnl


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
    """Placeholder until the shared market layer (Claude) lands in Phase 2."""
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


def compose_briefing(portfolio: Portfolio) -> BriefingResponse:
    quote = fx.get_eur_usd()
    positions = list(portfolio.positions)

    total_value_eur = sum(
        (pnl.market_value_eur(p) for p in positions), start=Decimal("0")
    )
    total_cost_eur = sum(
        (pnl.cost_basis_eur(p) for p in positions), start=Decimal("0")
    )

    # WoW delta requires a previous snapshot; until snapshots are persisted we
    # show zero so the UI shape is stable.
    wow_delta_eur = Decimal("0")
    wow_pct = Decimal("0")

    items = concentration.detect_concentration(positions, total_value_eur)

    sections: list[BriefingSection] = [
        _build_headline(total_value_eur, wow_delta_eur, wow_pct),
        _build_what_changed_placeholder(),
        _build_concentration_section(items),
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
