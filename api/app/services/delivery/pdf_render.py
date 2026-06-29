"""Render a BriefingResponse into a calm one-page PDF.

Pure and deterministic — mirrors the in-app briefing and the email: one hero
number, then the narrative sections, then disclaimers. Built with fpdf2 (pure
Python, no system deps, no headless browser) so it renders identically on
Windows dev and a Linux container.

fpdf2's core fonts (Helvetica) are latin-1 only, so text is sanitised first:
the euro sign and the smart punctuation that creeps in from news titles are
mapped to safe equivalents and anything else outside latin-1 is dropped. The
**bold** markers the briefing emits are rendered via multi_cell(markdown=True).
"""

from __future__ import annotations

import re
from decimal import Decimal

from fpdf import FPDF

from app.schemas import BriefingResponse

# Unicode the briefing/news can contain → latin-1-safe equivalents.
_REPLACEMENTS = {
    "€": "EUR ",  # €
    "—": "-",  # — em dash
    "–": "-",  # – en dash
    "‘": "'",  # ‘
    "’": "'",  # ’
    "“": '"',  # “
    "”": '"',  # ”
    "…": "...",  # …
    "•": "-",  # • bullet
    " ": " ",  # non-breaking space
}

_BLANKLINE = re.compile(r"\n\s*\n")

# A muted, calm palette to match the app — RGB tuples.
_INK = (26, 26, 26)
_BODY = (58, 58, 58)
_MUTED = (107, 107, 107)
_RULE = (224, 220, 208)


def _safe(text: str) -> str:
    """Make text printable with fpdf2's core latin-1 fonts (never raises)."""
    for bad, good in _REPLACEMENTS.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")


def _line(pdf: FPDF, height: float, text: str, *, markdown: bool = False) -> None:
    """Full-width line that always returns the cursor to the left margin.

    Without new_x=LMARGIN, multi_cell leaves X at the right margin, so the next
    full-width call would see ~0 width and raise.
    """
    pdf.multi_cell(0, height, _safe(text), markdown=markdown, new_x="LMARGIN", new_y="NEXT")


def _eur(amount) -> str:
    # Sanitisation turns "€" into "EUR ", so format with the symbol and let _safe map it.
    return f"€{Decimal(amount):,.2f}"


def _wow_line(b: BriefingResponse) -> str:
    if not b.wow_available:
        return "Week-over-week starts once your history builds"
    pct = Decimal(b.wow_delta_pct)
    sign = "+" if pct >= 0 else ""
    since = f" · since {b.wow_baseline_date}" if b.wow_baseline_date else ""
    return f"{sign}{pct}% ({sign}{_eur(b.wow_delta.eur)}){since}"


def _render_body(pdf: FPDF, markdown: str) -> None:
    """Render a section body: paragraphs, ## headings, and - bullet lists."""
    for block in _BLANKLINE.split(markdown.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        if all(ln.lstrip().startswith("- ") for ln in lines):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*_BODY)
            for ln in lines:
                _line(pdf, 5.2, "- " + ln.lstrip()[2:], markdown=True)
        elif block.startswith("## "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*_INK)
            _line(pdf, 6, block[3:], markdown=True)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*_BODY)
            _line(pdf, 5.2, " ".join(lines), markdown=True)
        pdf.ln(1.5)


def render_briefing_pdf(briefing: BriefingResponse) -> bytes:
    """Render the briefing to PDF bytes (starts with the %PDF- magic header)."""
    pdf = FPDF(format="A4")
    # EU AI Act Art. 50: mark the document as AI-assisted in its metadata.
    pdf.set_title("Sunday Portfolio Briefing")
    pdf.set_author("Sunday")
    pdf.set_creator("Sunday - generated with AI assistance (Claude by Anthropic)")
    pdf.set_keywords("ai-generated portfolio-briefing")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    # Kicker.
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_MUTED)
    _line(pdf, 5, f"SUNDAY BRIEFING · WEEK OF {briefing.week_of}")
    pdf.ln(4)

    # Hero net worth.
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*_MUTED)
    _line(pdf, 5, "Net worth")
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*_INK)
    _line(pdf, 12, _eur(briefing.net_worth.eur))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*_MUTED)
    _line(pdf, 5, f"{_wow_line(briefing)} · EUR/USD {Decimal(briefing.fx_eur_usd):.4f}")
    pdf.ln(6)

    # Narrative sections (the headline is the hero, so skip it as a block).
    for section in briefing.sections:
        if section.kind == "headline":
            continue
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_MUTED)
        _line(pdf, 5, section.title.upper())
        pdf.ln(0.5)
        _render_body(pdf, section.body_markdown)
        pdf.ln(2.5)

    # Disclaimers, under a hairline rule.
    pdf.ln(2)
    y = pdf.get_y()
    pdf.set_draw_color(*_RULE)
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*_MUTED)
    _line(pdf, 4.4, " · ".join(briefing.disclaimers))
    _line(pdf, 4.4, "Generated with AI assistance (Claude by Anthropic). Information only.")

    return bytes(pdf.output())
