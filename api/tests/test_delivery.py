"""Tests for the delivery layer (services/delivery).

Pure and deterministic — no network, no email provider. Covers the markdown→HTML
conversion (incl. escaping), the email render, and the dry-run sender.
"""

from decimal import Decimal

from app.models import User
from app.schemas import BriefingResponse, BriefingSection
from app.schemas.portfolio import DualMoney
from app.services.delivery import briefing_delivery, email_render, markdown_lite, pdf_render, sender


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

    def test_ai_act_disclosure_present(self):
        # EU AI Act Art. 50: visible disclosure + machine-readable marker, in both parts.
        email = email_render.render_briefing_email(_briefing())
        assert "generated with AI assistance" in email.html
        assert "<!-- ai-generated: true -->" in email.html
        assert "Generated with AI assistance" in email.text


class TestPdfRender:
    def test_renders_a_valid_pdf(self):
        pdf = pdf_render.render_briefing_pdf(_briefing())
        # Valid PDF magic header and non-trivial content.
        assert pdf[:5] == b"%PDF-"
        assert pdf.rstrip().endswith(b"%%EOF")
        assert len(pdf) > 1000

    def test_handles_unicode_without_crashing(self):
        # €, em dash, and smart quotes must not raise with core latin-1 fonts.
        b = _briefing()
        b.sections[1].body_markdown = "**€** flows — “quoted” … bullet:\n\n- €1,000 move"
        pdf = pdf_render.render_briefing_pdf(b)
        assert pdf[:5] == b"%PDF-"

    def test_no_history_variant_renders(self):
        pdf = pdf_render.render_briefing_pdf(_briefing(wow_available=False))
        assert pdf[:5] == b"%PDF-"

    def test_ai_act_disclosure_in_metadata_and_body(self):
        # EU AI Act Art. 50: AI-assisted marking in the PDF metadata and a visible line.
        pdf = pdf_render.render_briefing_pdf(_briefing())
        assert b"AI assistance" in pdf  # Creator metadata + body line


class TestSenderDryRun:
    def test_no_key_is_dry_run_and_does_not_send(self):
        # Test env has no RESEND_API_KEY → dry-run, no network call.
        res = sender.send_email("user@example.com", "subj", "<p>hi</p>", "hi")
        assert res.ok is True
        assert res.dry_run is True
        assert res.message_id is None and res.error is None

    def test_dry_run_accepts_attachments(self):
        res = sender.send_email(
            "user@example.com", "subj", "<p>hi</p>", "hi",
            attachments=[("briefing.pdf", b"%PDF-1.7 ...")],
        )
        assert res.ok is True and res.dry_run is True


class TestWeeklyOptIn:
    def test_deliver_weekly_selects_only_opted_in_pro_users(self, db):
        # Opted-in Pro user has no portfolio -> fails fast (no briefing build, no
        # network), which still proves selection. The opted-out user is skipped, and
        # the opted-in *free* user is skipped too (weekly email is Pro-only).
        pro_in = User(email="pro@test.com", weekly_opt_in=True, subscription_status="active")
        free_in = User(email="free@test.com", weekly_opt_in=True)  # opted in but free
        opted_out = User(email="out@test.com", weekly_opt_in=False, subscription_status="active")
        db.add_all([pro_in, free_in, opted_out])
        db.commit()

        summary = briefing_delivery.deliver_weekly(db)

        assert summary.total == 1
        assert [r.email for r in summary.results] == ["pro@test.com"]
        assert summary.results[0].ok is False
        assert summary.results[0].error == "user has no portfolio"

    def test_deliver_weekly_empty_when_no_opt_ins(self, db):
        db.add(User(email="nobody@test.com", weekly_opt_in=False))
        db.commit()

        summary = briefing_delivery.deliver_weekly(db)

        assert summary.total == 0
        assert summary.sent == 0 and summary.failed == 0
