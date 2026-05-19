from decimal import Decimal

from app.models import Position
from app.services import concentration


def _position(ticker: str, quantity: Decimal, price: Decimal) -> Position:
    return Position(
        portfolio_id=1,
        ticker=ticker,
        asset_class="stock",
        currency="EUR",
        quantity=quantity,
        avg_cost_eur=price,
        last_price_eur=price,
    )


def test_detect_concentration_flags_above_alert_threshold() -> None:
    positions = [
        _position("BIG", Decimal("10"), Decimal("1000")),
        _position("MID", Decimal("10"), Decimal("100")),
        _position("SMALL", Decimal("10"), Decimal("10")),
    ]
    total = Decimal("11100")

    items = concentration.detect_concentration(positions, total)

    by_ticker = {i.ticker: i for i in items}
    assert by_ticker["BIG"].severity == "alert"
    assert by_ticker["MID"].severity == "warning"
    assert "SMALL" not in by_ticker


def test_asset_class_split_sums_to_100() -> None:
    positions = [
        _position("BIG", Decimal("10"), Decimal("100")),
        Position(
            portfolio_id=1,
            ticker="BTC",
            asset_class="crypto",
            currency="EUR",
            quantity=Decimal("1"),
            avg_cost_eur=Decimal("1000"),
            last_price_eur=Decimal("1000"),
        ),
    ]
    total = Decimal("2000")

    split = concentration.asset_class_split(positions, total)

    assert split["stock"] == Decimal("50.00")
    assert split["crypto"] == Decimal("50.00")
