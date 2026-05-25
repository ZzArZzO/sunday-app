from decimal import Decimal

from app.models import Position
from app.services import dividend_projector


def _position(
    id_: int, ticker: str, asset_class: str, qty: Decimal, price: Decimal
) -> Position:
    return Position(
        id=id_,
        portfolio_id=1,
        ticker=ticker,
        asset_class=asset_class,
        currency="EUR",
        quantity=qty,
        avg_cost_eur=price,
        last_price_eur=price,
    )


def test_known_ticker_uses_override_yield() -> None:
    pos = _position(1, "NESN", "stock", Decimal("10"), Decimal("100"))
    lines = dividend_projector.project([pos], {1: Decimal("1000")})

    assert lines[0].source == "known"
    assert lines[0].yield_pct == Decimal("3.20")
    assert lines[0].annual_dividend_eur == Decimal("32.00")


def test_unknown_ticker_falls_back_to_asset_class_yield() -> None:
    pos = _position(2, "RANDOM", "stock", Decimal("10"), Decimal("100"))
    lines = dividend_projector.project([pos], {2: Decimal("1000")})

    assert lines[0].source == "estimate"
    assert lines[0].yield_pct == dividend_projector.ASSET_CLASS_YIELD_PCT["stock"]


def test_crypto_has_zero_yield() -> None:
    pos = _position(3, "BTC", "crypto", Decimal("0.5"), Decimal("60000"))
    lines = dividend_projector.project([pos], {3: Decimal("30000")})

    assert lines[0].annual_dividend_eur == Decimal("0.00")


def test_total_annual_sums_lines() -> None:
    a = _position(1, "NESN", "stock", Decimal("10"), Decimal("100"))
    b = _position(2, "VHYL", "etf", Decimal("5"), Decimal("100"))
    lines = dividend_projector.project([a, b], {1: Decimal("1000"), 2: Decimal("500")})

    expected = lines[0].annual_dividend_eur + lines[1].annual_dividend_eur
    assert dividend_projector.total_annual_eur(lines) == expected


def test_weighted_yield_handles_empty_portfolio() -> None:
    assert dividend_projector.weighted_yield_pct([]) == Decimal("0")
