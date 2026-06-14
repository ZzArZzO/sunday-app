"""Tests for the delivery layer (services/delivery).

Pure and deterministic — no network, no email provider. Covers the markdown→HTML
conversion (incl. escaping), the email render, and the dry-run sender.
"""

from decimal import Decimal

from app.schemas import BriefingResponse, BriefingSection
from app.schemas.portfolio import DualMoney
from app.services.delivery import email_render, markdown_lite, sender


class TestMarkdownLite:
    def test_bold_and_bullets(self):
        html = markdown_lite.to_html("**Headlines:**\n\n- **AAPL** — up\n- BTC — down")
        assert "<strong>Headlines:</strong>" in html
        assert "<ul" in html and "<li" in html
        assert "<strong>AAPL</strong>" in html

    def test_escapes_html_injection(self):
        html = markdown_lite.to_html("News: <script>alert(1)</script> & co")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html and "&amp;" in html

    def test_to_text_strips_bold(self):
        assert markdown_lite.to_text("**bold** plain") == "bold plain"


def _briefing(wow_available: bool = True) -> BriefingResponse:
    dm = DualMoney(eur=Decimal("24317.79"), usd=Decimal("28142.33"))
    delta = DualMoney(eur=Decimal("310.50"), usd=Decimal("359.00"))
    return BriefingResponse(
        portfolio_id=1,
        week_of="2026-06-14",
        generated_at="2026-06-14T12:00:00+00:00",
        fx_eur_usd=Decimal("1.1573"),
        net_worth=dm,
        wow_delta=delta,
        wow_delta_pct=Decimal("1.29"),
        wow_available=wow_available,
        wow_baseline_date="2026-06-07" if wow_available else None,
        sections=[
            BriefingSection(kind="headline", title="hero", body_markdown="HIDDEN"),
            BriefingSection(kind="what_changed", title="What changed this week",
                            body_markdown="**Headlines:**\n\n- **ASML** — Mistral stake"),
            BriefingSection(kind="regime", title="Market regime", body_markdown="Neutral-to-mixed."),
        ],
        concentration_alerts=[],
        disclaimers=["Not investment advice. Information only.", "Generated with AI assistance."],
    )


class TestEmailRender:
    def test_renders_hero_sections_and_disclaimers(self):
        email = email_render.render_briefing_email(_briefing())
        assert "week of 2026-06-14" in email.subject
        # Hero number + WoW.
        assert "€24,317.79" in email.html
        assert "1.29%" in email.html and "since 2026-06-07" in email.html
        # Sections rendered, headline hidden.
        assert "What changed this week" in email.html
        assert "<strong>ASML</strong>" in email.html
        assert "Market regime" in email.html
        assert "HIDDEN" not in email.html
        # Disclaimers present.
        assert "Not investment advice" in email.html
        # Plain-text alternative exists and is non-trivial.
        assert "Net worth: €24,317.79" in email.text

    def test_no_history_wow_copy(self):
        email = email_render.render_briefing_email(_briefing(wow_available=False))
        assert "Week-over-week starts once your history builds" in email.html


class TestSenderDryRun:
    def test_no_key_is_dry_run_and_does_not_send(self):
        # Test env has no RESEND_API_KEY → dry-run, no network call.
        res = sender.send_email("user@example.com", "subj", "<p>hi</p>", "hi")
        assert res.ok is True
        assert res.dry_run is True
        assert res.message_id is None and res.error is None
