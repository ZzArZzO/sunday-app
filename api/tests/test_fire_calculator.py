from decimal import Decimal

from app.services import fire_calculator


def _inputs(**overrides) -> fire_calculator.FireInputs:
    base = dict(
        current_net_worth_eur=Decimal("50000"),
        annual_expenses_eur=Decimal("30000"),
        annual_savings_eur=Decimal("12000"),
        expected_real_return_pct=Decimal("5.00"),
        safe_withdrawal_rate_pct=Decimal("4.00"),
        current_age=None,
    )
    base.update(overrides)
    return fire_calculator.FireInputs(**base)


def test_full_fire_number_uses_25x_at_4pct_swr() -> None:
    calc = fire_calculator.calculate(_inputs(annual_expenses_eur=Decimal("40000")))
    assert calc.full_fire_eur == Decimal("1000000.00")


def test_full_fire_number_scales_with_swr() -> None:
    calc = fire_calculator.calculate(
        _inputs(
            annual_expenses_eur=Decimal("40000"),
            safe_withdrawal_rate_pct=Decimal("5.00"),
        )
    )
    # 40,000 / 5% = 800,000
    assert calc.full_fire_eur == Decimal("800000.00")


def test_progress_is_zero_when_no_net_worth() -> None:
    calc = fire_calculator.calculate(_inputs(current_net_worth_eur=Decimal("0")))
    assert calc.full_fire_progress_pct == Decimal("0.00")


def test_years_to_full_fire_returns_finite_estimate() -> None:
    calc = fire_calculator.calculate(_inputs())
    assert calc.years_to_full_fire is not None
    assert calc.years_to_full_fire > 0
    assert calc.years_to_full_fire < Decimal("100")


def test_lean_and_fat_are_multiples_of_full() -> None:
    calc = fire_calculator.calculate(_inputs(annual_expenses_eur=Decimal("40000")))
    assert calc.lean_fire_eur == (calc.full_fire_eur * Decimal("0.6")).quantize(Decimal("0.01"))
    assert calc.fat_fire_eur == (calc.full_fire_eur * Decimal("2")).quantize(Decimal("0.01"))


def test_timeline_grows_monotonically() -> None:
    calc = fire_calculator.calculate(_inputs())
    values = [p.projected_net_worth_eur for p in calc.timeline]
    assert values == sorted(values)
    assert len(values) == fire_calculator.TIMELINE_MAX_YEARS + 1


def test_missing_inputs_emit_notes() -> None:
    calc = fire_calculator.calculate(
        _inputs(annual_expenses_eur=None, annual_savings_eur=None)
    )
    assert len(calc.notes) == 2
