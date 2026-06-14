"""Tests for the chat assistant's deterministic grounding (services/llm/portfolio_context).

Pure: `build_grounding` runs over in-memory Position objects plus duck-typed
snapshot stand-ins, so no DB is needed.
"""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.models import Position
from app.services.llm import portfolio_context


def _pos(ticker: str, asset_class: str, qty: str, price: str) -> Position:
    return Position(
        id=abs(hash(ticker)) % 100000,
        ticker=ticker,
        asset_class=asset_class,
        quantity=Decimal(qty),
        avg_cost_eur=Decimal(price),
        last_price_eur=Decimal(price),
    )


def test_grounding_empty_portfolio_has_no_holdings():
    pf = SimpleNamespace(positions=[], snapshots=[])
    g = portfolio_context.build_grounding(pf)
    assert g.holdings == []
    assert g.as_of is None
    assert g.facts and "No holdings" in g.facts[0]


def test_grounding_lists_holdings_weights_and_facts():
    positions = [
        _pos("AAPL", "stock", "10", "100"),  # value 1000
        _pos("BTC", "crypto", "1", "1000"),  # value 1000
    ]
    snap = SimpleNamespace(as_of=datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc))
    pf = SimpleNamespace(positions=positions, snapshots=[snap])

    g = portfolio_context.build_grounding(pf)

    assert {h.ticker for h in g.holdings} == {"AAPL", "BTC"}
    # Two equal holdings → 50% each, summing to 100%.
    assert sum(h.weight_pct for h in g.holdings) == Decimal("100.00")
    assert g.as_of == snap.as_of.isoformat()
    assert any("Total value" in f for f in g.facts)
    assert any("Asset split" in f for f in g.facts)
