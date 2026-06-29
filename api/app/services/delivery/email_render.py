"""Render a BriefingResponse into a calm HTML + plain-text email.

Pure and deterministic. Mirrors the in-app briefing: one hero number, then the
narrative sections, then disclaimers. Inline styles only (email clients strip
<style>). The headline section is the hero, so it's not repeated as a block.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.schemas import BriefingResponse
from app.services.delivery import markdown_lite

_BG = "#f4f1ea"
_CARD = "#ffffff"
_INK = "#1a1a1a"
_MUTED = "#6b6b6b"


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    html: str
    text: str


def _eur(amount) -> str:
    return f"€{Decimal(amount):,.2f}"


def _wow_line(b: BriefingResponse) -> str:
    if not b.wow_available:
        return "Week-over-week starts once your history builds"
    pct = Decimal(b.wow_delta_pct)
    sign = "+" if pct >= 0 else ""
    since = f" · since {b.wow_baseline_date}" if b.wow_baseline_date else ""
    return f"{sign}{pct}% ({sign}{_eur(b.wow_delta.eur)}){since}"


def render_briefing_email(briefing: BriefingResponse) -> RenderedEmail:
    subject = f"Your Sunday briefing — week of {briefing.week_of}"

    section_blocks = []
    for s in briefing.sections:
        if s.kind == "headline":
            continue
        section_blocks.append(
            f"<div style='margin:0 0 26px'>"
            f"<div style='font-size:11px;letter-spacing:.08em;text-transform:uppercase;"
            f"color:{_MUTED};margin:0 0 6px'>{s.title}</div>"
            f"{markdown_lite.to_html(s.body_markdown)}"
            f"</div>"
        )
    sections_html = "\n".join(section_blocks)
    disclaimers_html = " · ".join(briefing.disclaimers)
    # EU AI Act Art. 50: visible AI disclosure + machine-readable marker.
    ai_disclosure_html = (
        f"<p style='margin:6px 0 0;color:{_MUTED}'>This briefing was generated with AI "
        f"assistance (Claude by Anthropic). Information only, not investment advice.</p>"
        "<!-- ai-generated: true -->"
    )

    html = f"""\
<div style="margin:0;padding:24px 0;background:{_BG};font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">
  <div style="max-width:560px;margin:0 auto;background:{_CARD};border-radius:14px;overflow:hidden;border:1px solid #e7e2d6">
    <div style="padding:28px 28px 8px">
      <div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:{_MUTED}">
        Sunday briefing · week of {briefing.week_of}
      </div>
      <div style="font-size:13px;color:{_MUTED};margin:18px 0 4px">Net worth</div>
      <div style="font-size:38px;font-weight:600;letter-spacing:-.02em;color:{_INK};line-height:1.1">
        {_eur(briefing.net_worth.eur)}
      </div>
      <div style="font-size:14px;color:{_MUTED};margin:8px 0 0">
        {_wow_line(briefing)} · EUR/USD {Decimal(briefing.fx_eur_usd):.4f}
      </div>
    </div>
    <div style="padding:20px 28px 8px">
      {sections_html}
    </div>
    <div style="padding:18px 28px 26px;border-top:1px solid #efeae0;font-size:12px;color:{_MUTED};line-height:1.5">
      {disclaimers_html}
      {ai_disclosure_html}
    </div>
  </div>
  <div style="max-width:560px;margin:14px auto 0;text-align:center;font-size:12px;color:{_MUTED}">
    Sunday — a quiet portfolio briefing, every Sunday.
  </div>
</div>"""

    # Plain-text alternative.
    text_lines = [
        f"Sunday briefing — week of {briefing.week_of}",
        "",
        f"Net worth: {_eur(briefing.net_worth.eur)}",
        f"Week over week: {_wow_line(briefing)}",
        "",
    ]
    for s in briefing.sections:
        if s.kind == "headline":
            continue
        text_lines.append(s.title.upper())
        text_lines.append(markdown_lite.to_text(s.body_markdown))
        text_lines.append("")
    text_lines.append("— " + disclaimers_html)
    text_lines.append(
        "Generated with AI assistance (Claude by Anthropic). Information only, not investment advice."
    )
    text = "\n".join(text_lines)

    return RenderedEmail(subject=subject, html=html, text=text)
