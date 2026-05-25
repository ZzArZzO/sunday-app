from decimal import Decimal

from app.models import Position, User
from app.services import rebalancer


def _user(**targets) -> User:
    base = dict(
        target_etf_pct=Decimal("60.00"),
        target_stock_pct=Decimal("20.00"),
        target_crypto_pct=Decimal("15.00"),
        target_cash_pct=Decimal("5.00"),
    )
    base.update(targets)
    return User(
        id=1,
        email="t@test.local",
        country="DE",
        timezone="Europe/Berlin",
        expected_real_return_pct=Decimal("5.00"),
        safe_withdrawal_rate_pct=Decimal("4.00"),
        **base,
    )


def _position(asset_class: str, qty: Decimal, price: Decimal, ticker: str = "X") -> Position:
    return Position(
        portfolio_id=1,
        ticker=ticker,
        asset_class=asset_class,
        currency="EUR",
        quantity=qty,
        avg_cost_eur=price,
        last_price_eur=price,
    )


def test_perfect_alignment_means_no_rebalance_needed() -> None:
    positions = [
        _position("etf", Decimal("60"), Decimal("100"), "VWCE"),
        _position("stock", Decimal("20"), Decimal("100"), "ASML"),
        _position("crypto", Decimal("15"), Decimal("100"), "BTC"),
        _position("cash", Decimal("5"), Decimal("100"), "EUR"),
    ]
    calc = rebalancer.suggest(positions, _user())

    assert calc.needs_rebalance is False
    assert all(leg.action == "hold" for leg in calc.legs)


def test_overweight_triggers_sell() -> None:
    # 100% crypto, 60/20/15/5 target — crypto is way overweight, needs sell.
    positions = [_position("crypto", Decimal("100"), Decimal("100"), "BTC")]
    calc = rebalancer.suggest(positions, _user())

    crypto_leg = next(leg for leg in calc.legs if leg.asset_class == "crypto")
    etf_leg = next(leg for leg in calc.legs if leg.asset_class == "etf")
    assert crypto_leg.action == "sell"
    assert etf_leg.action == "buy"
    assert calc.needs_rebalance is True


def test_drift_score_is_zero_for_aligned_portfolio() -> None:
    positions = [
        _position("etf", Decimal("60"), Decimal("100"), "VWCE"),
        _position("stock", Decimal("20"), Decimal("100"), "ASML"),
        _position("crypto", Decimal("15"), Decimal("100"), "BTC"),
        _position("cash", Decimal("5"), Decimal("100"), "EUR"),
    ]
    calc = rebalancer.suggest(positions, _user())
    assert calc.drift_score == Decimal("0.00")


def test_empty_portfolio_produces_no_legs() -> None:
    calc = rebalancer.suggest([], _user())
    assert calc.legs == []
    assert calc.needs_rebalance is False


def test_targets_normalised_when_sum_is_off() -> None:
    user = _user(
        target_etf_pct=Decimal("50.00"),
        target_stock_pct=Decimal("30.00"),
        target_crypto_pct=Decimal("10.00"),
        target_cash_pct=Decimal("10.00"),  # sums to 100
    )
    positions = [_position("etf", Decimal("50"), Decimal("100"), "VWCE")]
    calc = rebalancer.suggest(positions, user)
    assert all(0 <= leg.target_pct <= 100 for leg in calc.legs)
