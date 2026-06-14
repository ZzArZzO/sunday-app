"""Tests for the MiFID II / MiCA output guardrail (services/llm/guardrails.py).

These are pure and deterministic — no Anthropic calls. They protect the bright
line in docs/LEGAL.md: model output must never read as a personal recommendation.
"""

from app.services.llm import guardrails


class TestScanFlagsAdvice:
    def test_you_should_is_flagged(self):
        result = guardrails.scan("Your NVDA position is large, so you should trim it.")
        assert not result.clean
        assert result.violations

    def test_consider_selling_is_flagged(self):
        result = guardrails.scan("Consider selling some of your crypto here.")
        assert not result.clean

    def test_i_recommend_is_flagged(self):
        result = guardrails.scan("I recommend rotating into bonds.")
        assert not result.clean

    def test_take_profits_is_flagged(self):
        result = guardrails.scan("This looks like a good place to take profits.")
        assert not result.clean

    def test_good_time_to_buy_is_flagged(self):
        result = guardrails.scan("It's a good time to buy the dip.")
        assert not result.clean


class TestScanAllowsInformation:
    def test_factual_statement_is_clean(self):
        result = guardrails.scan(
            "Your tech allocation is 64%. Concentration above ~10% in one name is "
            "generally considered elevated because it raises single-stock risk."
        )
        assert result.clean
        assert result.violations == []

    def test_definition_is_clean(self):
        result = guardrails.scan(
            "CPI measures consumer price inflation. A hotter print often pressures "
            "rate-sensitive assets."
        )
        assert result.clean

    def test_compliant_refusal_does_not_false_positive(self):
        # The model's own disclaimer must not trip the filter.
        result = guardrails.scan(
            "I can't give personalised recommendations, but I can explain how "
            "concentration risk works."
        )
        assert result.clean

    def test_safe_fallback_reply_is_itself_clean(self):
        # The canned fallback must pass its own filter, or we'd loop forever.
        result = guardrails.scan(guardrails.SAFE_FALLBACK_REPLY)
        assert result.clean
