from decimal import Decimal

from app.services import tax_summary


def test_germany_applies_allowance_before_tax() -> None:
    profile = tax_summary.profile_for("DE")
    # Gains of 500 are within the 1000 allowance — no tax.
    calc = tax_summary.estimate_tax_on_unrealised(
        profile,
        unrealised_gains_eur=Decimal("500"),
        market_value_eur=Decimal("10000"),
    )
    assert calc.tax_due_eur == Decimal("0.00")
    assert calc.after_tax_value_eur == Decimal("10000.00")


def test_germany_taxes_above_allowance() -> None:
    profile = tax_summary.profile_for("DE")
    calc = tax_summary.estimate_tax_on_unrealised(
        profile,
        unrealised_gains_eur=Decimal("2000"),
        market_value_eur=Decimal("10000"),
    )
    # Taxable: 2000 - 1000 = 1000; tax 1000 * 26.375% = 263.75
    assert calc.tax_due_eur == Decimal("263.75")


def test_germany_teilfreistellung_reduces_etf_gains() -> None:
    profile = tax_summary.profile_for("DE")
    calc_full = tax_summary.estimate_tax_on_unrealised(
        profile,
        unrealised_gains_eur=Decimal("10000"),
        market_value_eur=Decimal("100000"),
    )
    calc_etf = tax_summary.estimate_tax_on_unrealised(
        profile,
        unrealised_gains_eur=Decimal("10000"),
        market_value_eur=Decimal("100000"),
        equity_etf_share_pct=Decimal("100"),
    )
    # ETF gains get a 30% exemption — should owe less.
    assert calc_etf.tax_due_eur < calc_full.tax_due_eur


def test_france_has_no_allowance_and_flat_rate() -> None:
    profile = tax_summary.profile_for("FR")
    assert profile.annual_allowance_eur == Decimal("0")
    calc = tax_summary.estimate_tax_on_unrealised(
        profile,
        unrealised_gains_eur=Decimal("1000"),
        market_value_eur=Decimal("10000"),
    )
    # 1000 * 30% = 300
    assert calc.tax_due_eur == Decimal("300.00")


def test_unknown_country_falls_back_to_default() -> None:
    assert tax_summary.profile_for("ZZ").code == "DE"


def test_loss_produces_no_tax() -> None:
    profile = tax_summary.profile_for("DE")
    calc = tax_summary.estimate_tax_on_unrealised(
        profile,
        unrealised_gains_eur=Decimal("-500"),
        market_value_eur=Decimal("10000"),
    )
    assert calc.tax_due_eur == Decimal("0")
    assert calc.taxable_gains_eur == Decimal("0")
