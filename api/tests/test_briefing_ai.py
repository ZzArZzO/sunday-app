"""Tests for the AI briefing layer (services/llm/briefing_ai).

Pure and deterministic — no network, no LLM. Covers the merge logic, the
guardrail accept/reject decision, and the no-API-key fallback (the briefing must
render the deterministic version when AI is unavailable).
"""

from decimal import Decimal
from types import SimpleNamespace

from app.schemas import BriefingResponse, BriefingSection
from app.schemas.portfolio import DualMoney
from app.services.llm.briefing_ai import NarrativeOut, _accept, apply_narrative, enhance


def _response() -> BriefingResponse:
    dm = DualMoney(eur=Decimal("0"), usd=Decimal("0"))
    return BriefingResponse(
        portfolio_id=1,
        week_of="2026-06-14",
        generated_at="2026-06-14T12:00:00+00:00",
        fx_eur_usd=Decimal("1.10"),
        net_worth=dm,
        wow_delta=dm,
        wow_delta_pct=Decimal("0"),
        wow_available=False,
        wow_baseline_date=None,
        sections=[
            BriefingSection(kind="headline", title="x", body_markdown="HEADLINE"),
            BriefingSection(kind="what_changed", title="What changed", body_markdown="PLACEHOLDER_WC"),
            BriefingSection(kind="regime", title="Regime", body_markdown="PLACEHOLDER_REGIME"),
            BriefingSection(kind="tax_flags", title="Tax", body_markdown="TAXBODY"),
        ],
        concentration_alerts=[],
        disclaimers=["Not investment advice. Information only."],
    )


class TestApplyNarrative:
    def test_replaces_only_the_two_placeholder_sections(self):
        out = apply_narrative(_response(), NarrativeOut(this_week="THIS WEEK", regime="REGIME"))
        by_kind = {s.kind: s.body_markdown for s in out.sections}
        assert by_kind["what_changed"] == "THIS WEEK"
        assert by_kind["regime"] == "REGIME"
        assert by_kind["tax_flags"] == "TAXBODY"  # untouched
        assert by_kind["headline"] == "HEADLINE"  # untouched
        assert "Generated with AI assistance." in out.disclaimers

    def test_does_not_mutate_input(self):
        resp = _response()
        apply_narrative(resp, NarrativeOut(this_week="A", regime="B"))
        wc = next(s for s in resp.sections if s.kind == "what_changed")
        assert wc.body_markdown == "PLACEHOLDER_WC"  # original untouched


class TestAccept:
    def test_clean_narrative_accepted(self):
        n = NarrativeOut(
            this_week="CPI prints this week; your global-equity tilt means rate moves matter.",
            regime="Volatility is low, a generally calm environment.",
        )
        assert _accept(n) is True

    def test_advice_narrative_rejected(self):
        n = NarrativeOut(this_week="You should sell your crypto now.", regime="ok")
        assert _accept(n) is False

    def test_empty_section_rejected(self):
        assert _accept(NarrativeOut(this_week="", regime="ok")) is False


class TestEnhanceNoKey:
    def test_no_api_key_returns_deterministic_unchanged(self):
        # The test env has no ANTHROPIC_API_KEY → enhance must no-op (no network).
        resp = _response()
        out, used = enhance(resp, SimpleNamespace(id=1))
        assert used is False
        assert out is resp  # same object — nothing added
