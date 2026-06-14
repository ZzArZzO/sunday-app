"""Tests for the live-price layer (services/prices).

Pure and deterministic — a fake provider stands in for yfinance, so nothing
hits the network. Covers currency conversion and the position-pricing core.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.models import Position
from app.services.prices.base import Quote
from app.services.prices.convert import to_eur
from app.services.prices.refresh import price_positions
from app.services.prices.symbols import candidate_symbols

RATE = Decimal("1.08")  # USD per 1 EUR
GBP_EUR = Decimal("1.17")
NOW = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)


class FakeProvider:
    """Maps exact symbols to quotes; anything else is unavailable."""

    def __init__(self, quotes: dict[str, Quote]):
        self._quotes = quotes

    def get_quote(self, symbol: str) -> Quote | None:
        return self._quotes.get(symbol)


def _q(symbol: str, price: str, currency: str) -> Quote:
    return Quote(symbol, Decimal(price), currency, "fake")


class TestToEur:
    def test_eur_passthrough(self):
        assert to_eur(Decimal("95"), "EUR", eur_usd_rate=RATE).eur == Decimal("95")

    def test_blank_currency_treated_as_eur(self):
        assert to_eur(Decimal("95"), "", eur_usd_rate=RATE).eur == Decimal("95")

    def test_usd_divides_by_rate(self):
        # 216 USD / 1.08 = 200 EUR
        assert to_eur(Decimal("216"), "USD", eur_usd_rate=RATE).eur == Decimal("200")

    def test_pence_divided_by_100_then_gbp(self):
        # 500 GBp = 5 GBP × 1.17 = 5.85 EUR
        res = to_eur(Decimal("500"), "GBp", eur_usd_rate=RATE, cross_rates={"GBP": GBP_EUR})
        assert res.eur == Decimal("5.85")

    def test_pence_without_gbp_rate_is_a_note(self):
        res = to_eur(Decimal("500"), "GBp", eur_usd_rate=RATE, cross_rates=None)
        assert res.eur is None and res.note

    def test_chf_via_cross_rates(self):
        # 79.81 CHF × 1.084 = 86.51404 EUR
        res = to_eur(Decimal("79.81"), "CHF", eur_usd_rate=RATE, cross_rates={"CHF": Decimal("1.084")})
        assert res.eur == Decimal("86.51404")

    def test_unsupported_currency_returns_note(self):
        res = to_eur(Decimal("100"), "JPY", eur_usd_rate=RATE)
        assert res.eur is None and "JPY" in res.note


class TestPricePositions:
    def _positions(self) -> list[Position]:
        return [
            Position(id=1, ticker="BTC", asset_class="crypto", quantity=Decimal("0.5"), avg_cost_eur=Decimal("28500")),
            Position(id=2, ticker="SOL", asset_class="crypto", quantity=Decimal("10"), avg_cost_eur=Decimal("85")),
            Position(id=3, ticker="AAPL", asset_class="stock", quantity=Decimal("3"), avg_cost_eur=Decimal("150")),
            Position(id=4, ticker="EUNL", asset_class="etf", quantity=Decimal("20"), avg_cost_eur=Decimal("90")),
            Position(id=5, ticker="", asset_class="stock", quantity=Decimal("1"), avg_cost_eur=Decimal("10")),
        ]

    def test_prices_each_class_and_converts(self):
        provider = FakeProvider({
            "BTC-EUR": _q("BTC-EUR", "90000", "EUR"),   # crypto, native EUR
            "SOL-USD": _q("SOL-USD", "216", "USD"),     # crypto, USD only → /1.08
            "AAPL": _q("AAPL", "216", "USD"),           # US stock in USD
            "EUNL": _q("EUNL", "95", "EUR"),            # EU ETF in EUR
        })
        positions = self._positions()
        result = price_positions(
            positions, provider, eur_usd_rate=RATE, cross_rates={"GBP": GBP_EUR}, now=NOW
        )

        by_id = {p.id: p for p in positions}
        assert by_id[1].last_price_eur == Decimal("90000.0000")
        assert by_id[2].last_price_eur == Decimal("200.0000")
        assert by_id[3].last_price_eur == Decimal("200.0000")
        assert by_id[4].last_price_eur == Decimal("95.0000")
        assert by_id[1].last_price_at == NOW

        assert result.priced == 4
        assert result.unpriced == 1  # the tickerless position
        assert result.total == 5
        assert any("UNPRICED" in w for w in result.warnings)

    def test_crypto_prefers_eur_pair_then_falls_back_to_usd(self):
        provider = FakeProvider({"SOL-USD": _q("SOL-USD", "216", "USD")})
        pos = [Position(id=2, ticker="SOL", asset_class="crypto", quantity=Decimal("1"), avg_cost_eur=Decimal("0"))]
        price_positions(pos, provider, eur_usd_rate=RATE, cross_rates=None, now=NOW)
        assert pos[0].last_price_eur == Decimal("200.0000")

    def test_unresolved_ticker_leaves_price_untouched(self):
        provider = FakeProvider({})  # nothing resolves
        pos = [Position(id=9, ticker="ZZZZ", asset_class="stock", quantity=Decimal("1"), avg_cost_eur=Decimal("10"))]
        result = price_positions(pos, provider, eur_usd_rate=RATE, cross_rates=None, now=NOW)
        assert pos[0].last_price_eur is None  # falls back to cost basis in pnl.py
        assert result.unpriced == 1
        assert any("PRICE_FETCH_FAILED" in w for w in result.warnings)

    def test_eu_isin_and_chf_priced(self):
        # Mapped ISIN (VWCE.DE, EUR) + a CHF listing (NESN.SW) both price end-to-end.
        provider = FakeProvider({
            "VWCE.DE": _q("VWCE.DE", "162.46", "EUR"),
            "NESN.SW": _q("NESN.SW", "79.81", "CHF"),
        })
        pos = [
            Position(id=1, ticker="VWCE", isin="IE00BK5BQT80", asset_class="etf", quantity=Decimal("1"), avg_cost_eur=Decimal("100")),
            Position(id=2, ticker="NESN", isin="CH0038863350", asset_class="stock", quantity=Decimal("1"), avg_cost_eur=Decimal("90")),
        ]
        res = price_positions(pos, provider, eur_usd_rate=RATE, cross_rates={"CHF": Decimal("1.084")}, now=NOW)
        assert pos[0].last_price_eur == Decimal("162.4600")
        assert pos[1].last_price_eur == Decimal("86.5140")  # 79.81 × 1.084
        assert res.priced == 2


class TestCandidateSymbols:
    def test_crypto_pairs(self):
        p = Position(id=1, ticker="BTC", asset_class="crypto")
        assert candidate_symbols(p) == ["BTC-EUR", "BTC-USD"]

    def test_isin_map_takes_priority(self):
        p = Position(id=1, ticker="VWCE", isin="IE00BK5BQT80", asset_class="etf")
        cands = candidate_symbols(p)
        assert cands[0] == "VWCE.DE"
        assert "VWCE" in cands  # bare ticker still attempted

    def test_chf_listing_mapped(self):
        p = Position(id=1, ticker="NESN", isin="CH0038863350", asset_class="stock")
        assert candidate_symbols(p)[0] == "NESN.SW"

    def test_us_bare_ticker_first_then_eu_suffixes(self):
        p = Position(id=1, ticker="AAPL", asset_class="stock")
        cands = candidate_symbols(p)
        assert cands[0] == "AAPL"
        assert "AAPL.DE" in cands
