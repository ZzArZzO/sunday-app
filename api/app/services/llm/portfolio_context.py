"""Deterministic portfolio context for the AI assistant.

The assistant is *grounded* in the user's real holdings — but the numbers it
sees are computed in pure Python (same auditable layer as the briefing), never
by the model. This builds a compact, factual snapshot string the model receives
as context. Keeping it small controls token cost and shrinks the hallucination
surface: the model reasons over facts, it does not invent them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.models import Portfolio
from app.services import concentration, dividend_projector, fx, pnl, tax_summary

# How many individual holdings to enumerate before collapsing the tail.
_MAX_LISTED_HOLDINGS = 12


@dataclass(frozen=True)
class GroundingHolding:
    ticker: str
    weight_pct: Decimal


@dataclass(frozen=True)
class Grounding:
    """Structured, user-facing view of the deterministic facts the model saw.

    Mirrors the figures in `build_snapshot` but as data (not prose) so the chat
    UI can show "based on your portfolio as of X" under each answer.
    """

    as_of: str | None
    holdings: list[GroundingHolding] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)


def build_grounding(portfolio: Portfolio) -> Grounding:
    positions = list(portfolio.positions)
    snaps = list(portfolio.snapshots)
    as_of = snaps[-1].as_of.isoformat() if snaps else None

    if not positions:
        return Grounding(as_of=as_of, holdings=[], facts=["No holdings recorded yet."])

    total_value = sum((pnl.market_value_eur(p) for p in positions), start=Decimal("0"))
    weights = concentration.position_weights(positions, total_value)
    holdings = [
        GroundingHolding(ticker=pos.ticker, weight_pct=weight.quantize(Decimal("0.01")))
        for pos, weight in weights[:_MAX_LISTED_HOLDINGS]
    ]

    facts: list[str] = [f"Total value €{total_value:,.0f}"]
    split = concentration.asset_class_split(positions, total_value)
    if split:
        split_str = ", ".join(
            f"{cls} {pct:.0f}%"
            for cls, pct in sorted(split.items(), key=lambda kv: kv[1], reverse=True)
        )
        facts.append(f"Asset split: {split_str}")

    return Grounding(as_of=as_of, holdings=holdings, facts=facts)


def _fmt_eur(amount: Decimal) -> str:
    return f"€{amount:,.2f}"


def _fmt_pct(pct: Decimal) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def build_snapshot(portfolio: Portfolio) -> str:
    """Render a compact factual summary of the portfolio for the model.

    Returns plain text (not shown to the user). All figures are deterministic.
    """
    positions = list(portfolio.positions)
    user = portfolio.user
    country = user.country if user else "DE"

    if not positions:
        return (
            "The user has connected an account but has no holdings recorded yet. "
            "You can still answer general questions, but you have no portfolio "
            "data to reference."
        )

    total_value = sum((pnl.market_value_eur(p) for p in positions), start=Decimal("0"))
    total_cost = sum((pnl.cost_basis_eur(p) for p in positions), start=Decimal("0"))
    unrealised = total_value - total_cost
    unrealised_pct = (
        (unrealised / total_cost * Decimal("100")).quantize(Decimal("0.01"))
        if total_cost > 0
        else Decimal("0")
    )

    lines: list[str] = []
    lines.append("PORTFOLIO SNAPSHOT (all figures are exact, computed server-side):")
    lines.append(f"- Country of tax residence (user-set): {country}")
    lines.append(f"- Total value: {_fmt_eur(total_value)}")
    lines.append(
        f"- Total cost basis: {_fmt_eur(total_cost)} "
        f"(unrealised P&L {_fmt_eur(unrealised)}, {_fmt_pct(unrealised_pct)})"
    )

    # Asset-class split.
    split = concentration.asset_class_split(positions, total_value)
    if split:
        parts = ", ".join(
            f"{cls} {pct:.1f}%" for cls, pct in sorted(split.items(), key=lambda kv: kv[1], reverse=True)
        )
        lines.append(f"- Asset-class split: {parts}")

    # Holdings, largest first.
    weights = concentration.position_weights(positions, total_value)
    lines.append("- Holdings (largest first):")
    for pos, weight in weights[:_MAX_LISTED_HOLDINGS]:
        mv = pnl.market_value_eur(pos)
        upnl = pnl.unrealised_pnl_eur(pos)
        upnl_pct = (
            (upnl / pnl.cost_basis_eur(pos) * Decimal("100")).quantize(Decimal("0.01"))
            if pnl.cost_basis_eur(pos) > 0
            else Decimal("0")
        )
        lines.append(
            f"    - {pos.ticker} ({pos.asset_class}): {weight:.2f}% of portfolio, "
            f"value {_fmt_eur(mv)}, unrealised {_fmt_pct(upnl_pct)}"
        )
    remaining = len(weights) - _MAX_LISTED_HOLDINGS
    if remaining > 0:
        lines.append(f"    - …and {remaining} smaller holding(s).")

    # Concentration flags (user-configured thresholds; defaults here are placeholders).
    flags = concentration.detect_concentration(positions, total_value)
    if flags:
        flag_str = ", ".join(
            f"{f.ticker} {f.weight_pct:.1f}% ({f.severity})" for f in flags
        )
        lines.append(f"- Positions above the user's concentration thresholds: {flag_str}")
    else:
        lines.append("- No positions are above the user's concentration thresholds.")

    # Dividend estimate (indicative).
    mv_by_id = {p.id: pnl.market_value_eur(p) for p in positions}
    div_lines = dividend_projector.project(positions, mv_by_id)
    annual_div = dividend_projector.total_annual_eur(div_lines)
    if annual_div > 0:
        lines.append(
            f"- Indicative forward 12-month dividend income (estimate): {_fmt_eur(annual_div)}"
        )

    # Tax context (informational headline only).
    profile = tax_summary.profile_for(country)
    lines.append(
        f"- Tax context: {profile.name} headline rate ~{profile.base_rate_pct}% on gains; "
        f"annual allowance {_fmt_eur(profile.annual_allowance_eur)}. Informational only."
    )

    quote = fx.get_eur_usd()
    lines.append(f"- Reference FX EUR/USD: {quote.rate} (source: {quote.source}).")

    return "\n".join(lines)
