"""Tests for the LLM cost ledger pricing (services/llm/cost_ledger).

Pure: verifies USD cost is computed correctly from token counts and the model's
list price, including the cache-read (0.1x) and cache-write (1.25x) multipliers.
"""

from decimal import Decimal

import pytest

from app.services.llm import cost_ledger


class TestCostUsd:
    def test_sonnet_input_output(self):
        # 1000 in @ $3/1M + 500 out @ $15/1M = 0.003 + 0.0075 = 0.0105
        assert cost_ledger.cost_usd("claude-sonnet-4-6", 1000, 500, 0, 0) == Decimal("0.010500")

    def test_haiku_input_output(self):
        # 1000 in @ $1/1M + 500 out @ $5/1M = 0.001 + 0.0025 = 0.0035
        assert cost_ledger.cost_usd("claude-haiku-4-5", 1000, 500, 0, 0) == Decimal("0.003500")

    def test_cache_read_is_tenth_of_input(self):
        # 1000 cache-read on Sonnet = 1000 * $3/1M * 0.1 = 0.0003
        assert cost_ledger.cost_usd("claude-sonnet-4-6", 0, 0, 0, 1000) == Decimal("0.000300")

    def test_cache_write_is_1_25x_input(self):
        # 1000 cache-write on Sonnet = 1000 * $3/1M * 1.25 = 0.00375
        assert cost_ledger.cost_usd("claude-sonnet-4-6", 0, 0, 1000, 0) == Decimal("0.003750")

    def test_matches_measured_chat_call(self):
        # The verification run measured a Sonnet chat turn: in=951, out=490.
        assert cost_ledger.cost_usd("claude-sonnet-4-6", 951, 490, 0, 0) == Decimal("0.010203")

    @pytest.mark.parametrize(
        "model,tier_price_in",
        [("claude-opus-4-8", 5), ("claude-fable-5", 10), ("something-unknown", 3)],
    )
    def test_tier_resolution(self, model, tier_price_in):
        # 1M input tokens should cost exactly the per-1M input price; unknown -> sonnet ($3).
        assert cost_ledger.cost_usd(model, 1_000_000, 0, 0, 0) == Decimal(tier_price_in)


class TestTokenExtraction:
    def test_reads_object_usage(self):
        class U:
            input_tokens = 100
            output_tokens = 50
            cache_creation_input_tokens = 10
            cache_read_input_tokens = 5

        assert cost_ledger._tokens(U()) == (100, 50, 10, 5)

    def test_reads_dict_usage_with_missing_fields(self):
        assert cost_ledger._tokens({"input_tokens": 100, "output_tokens": 50}) == (100, 50, 0, 0)
