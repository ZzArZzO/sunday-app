"""EU capital-gains tax summary.

Per-country headline figures only. Real-product tax features will need full
holding-period tracking, partial-exemption rules (e.g. German Teilfreistellung
for equity ETFs), and broker-reported withholdings. This service is the
informational floor: "rough order of magnitude of what you'd owe if you sold today."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class TaxBracketSpec:
    label: str
    rate_pct: Decimal
    applies_to: str


@dataclass(frozen=True)
class CountryTaxProfile:
    code: str
    name: str
    base_rate_pct: Decimal
    annual_allowance_eur: Decimal
    dividend_rate_pct: Decimal
    brackets: list[TaxBracketSpec] = field(default_factory=list)
    # German Teilfreistellung: 30% of equity-ETF gains are exempt.
    equity_etf_partial_exemption_pct: Decimal = Decimal("0")
    # Days a privately-held crypto position must be held to become tax-free
    # (DE §23 EStG and PT both use 365). None where no such rule applies.
    crypto_tax_free_after_days: int | None = None
    # Optional caveat surfaced in the API notes for countries where a single flat
    # estimate is misleading (0% regimes, holding-period relief, special ETF rules).
    headline_note: str = ""


# Sources:
#   DE — Abgeltungsteuer 25% + 5.5% Soli (effective 26.375%) + Sparerpauschbetrag €1,000
#   FR — Flat tax PFU 30% (12.8% IR + 17.2% prélèvements sociaux)
#   ES — Savings tax brackets 19% / 21% / 23% / 27% / 28% (2024)
#   NL — Box 3 wealth tax (deemed return × 36%), not realisation-based — we simplify
#   IT — Capital gains 26%
#   PT — Capital gains 28% (or marginal IRS if held < 1y)
COUNTRY_PROFILES: dict[str, CountryTaxProfile] = {
    "DE": CountryTaxProfile(
        code="DE",
        name="Germany",
        base_rate_pct=Decimal("26.375"),
        annual_allowance_eur=Decimal("1000"),
        dividend_rate_pct=Decimal("26.375"),
        brackets=[
            TaxBracketSpec(
                label="Abgeltungsteuer",
                rate_pct=Decimal("25.00"),
                applies_to="Capital gains and dividends",
            ),
            TaxBracketSpec(
                label="Solidaritätszuschlag",
                rate_pct=Decimal("1.375"),
                applies_to="5.5% of Abgeltungsteuer",
            ),
        ],
        equity_etf_partial_exemption_pct=Decimal("30"),
        crypto_tax_free_after_days=365,
    ),
    "FR": CountryTaxProfile(
        code="FR",
        name="France",
        base_rate_pct=Decimal("30.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("30.00"),
        brackets=[
            TaxBracketSpec(
                label="Impôt sur le revenu (PFU)",
                rate_pct=Decimal("12.80"),
                applies_to="Capital gains and dividends",
            ),
            TaxBracketSpec(
                label="Prélèvements sociaux",
                rate_pct=Decimal("17.20"),
                applies_to="Capital gains and dividends",
            ),
        ],
    ),
    "ES": CountryTaxProfile(
        code="ES",
        name="Spain",
        base_rate_pct=Decimal("19.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("19.00"),
        brackets=[
            TaxBracketSpec(
                label="Up to €6,000",
                rate_pct=Decimal("19.00"),
                applies_to="Savings income",
            ),
            TaxBracketSpec(
                label="€6,000 – €50,000",
                rate_pct=Decimal("21.00"),
                applies_to="Savings income",
            ),
            TaxBracketSpec(
                label="€50,000 – €200,000",
                rate_pct=Decimal("23.00"),
                applies_to="Savings income",
            ),
            TaxBracketSpec(
                label="Above €200,000",
                rate_pct=Decimal("27.00"),
                applies_to="Savings income",
            ),
        ],
    ),
    "NL": CountryTaxProfile(
        code="NL",
        name="Netherlands",
        base_rate_pct=Decimal("36.00"),
        annual_allowance_eur=Decimal("57000"),  # Box 3 heffingvrij vermogen 2024
        dividend_rate_pct=Decimal("15.00"),
        brackets=[
            TaxBracketSpec(
                label="Box 3 deemed return × 36%",
                rate_pct=Decimal("36.00"),
                applies_to="Wealth above €57,000 — not realisation-based",
            ),
        ],
    ),
    "IT": CountryTaxProfile(
        code="IT",
        name="Italy",
        base_rate_pct=Decimal("26.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("26.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital gains",
                rate_pct=Decimal("26.00"),
                applies_to="All capital gains (12.5% for some government bonds)",
            ),
        ],
    ),
    "PT": CountryTaxProfile(
        code="PT",
        name="Portugal",
        base_rate_pct=Decimal("28.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("28.00"),
        brackets=[
            TaxBracketSpec(
                label="Flat rate (held > 365 days)",
                rate_pct=Decimal("28.00"),
                applies_to="Capital gains and dividends",
            ),
            TaxBracketSpec(
                label="Marginal IRS (held < 365 days)",
                rate_pct=Decimal("48.00"),
                applies_to="Short-term capital gains, top bracket",
            ),
        ],
        crypto_tax_free_after_days=365,
    ),
    # --- Remaining eurozone members (informational; sources below are 2024 rules).
    # Several countries exempt long-held securities (BE, CY, MT ~0%; LU >6mo; SK >1y;
    # HR >2y; SI sliding by holding years). The single-bracket estimate uses the
    # headline rate that applies to a near-term sale (conservative); holding-period
    # relief is surfaced in `brackets`/notes. EVERY profile needs a local tax
    # professional's review before launch.
    #   AT — KESt 27.5% on gains & dividends
    #   BE — no general CGT on shares for private long-term investors; dividends 30% (RV)
    #   HR — 10% if sold < 2 years (then exempt); dividends 10%
    #   CY — 0% CGT on securities; dividends SDC 17% (non-doms exempt)
    #   EE — 20% PIT on realised gains (22% from 2025); investment-account deferral
    #   FI — 30% to €30k, 34% above
    #   GR — 15% on securities gains (listed-share gains often exempt); dividends 5%
    #   IE — 33% CGT, €1,270 exemption; ETFs taxed 41% under deemed-disposal
    #   LV — 20% on gains and dividends
    #   LT — 15% (20% above €500k); €500 annual securities-gains exemption
    #   LU — gains tax-free if held > 6 months (non-substantial); dividends 50% exempt then progressive
    #   MT — no CGT on securities transfers; dividends under full imputation
    #   SK — 19% (exempt if held > 1 year on a regulated market); dividends 7%
    #   SI — 25% reducing with holding period (>15y → 0%); dividends 25%
    "AT": CountryTaxProfile(
        code="AT",
        name="Austria",
        base_rate_pct=Decimal("27.50"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("27.50"),
        brackets=[
            TaxBracketSpec(
                label="Kapitalertragsteuer (KESt)",
                rate_pct=Decimal("27.50"),
                applies_to="Capital gains and dividends",
            ),
        ],
    ),
    "BE": CountryTaxProfile(
        code="BE",
        name="Belgium",
        base_rate_pct=Decimal("0"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("30.00"),
        headline_note=(
            "Belgium levies no general capital-gains tax on shares held under normal "
            "private management, so the estimate shows €0. Dividends are still taxed at 30%."
        ),
        brackets=[
            TaxBracketSpec(
                label="No general capital-gains tax",
                rate_pct=Decimal("0"),
                applies_to="Normal private management of shares",
            ),
            TaxBracketSpec(
                label="Roerende voorheffing",
                rate_pct=Decimal("30.00"),
                applies_to="Dividends",
            ),
        ],
    ),
    "HR": CountryTaxProfile(
        code="HR",
        name="Croatia",
        base_rate_pct=Decimal("10.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("10.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital gains (held < 2 years)",
                rate_pct=Decimal("10.00"),
                applies_to="Securities sold within two years (exempt after); plus local surtax",
            ),
        ],
    ),
    "CY": CountryTaxProfile(
        code="CY",
        name="Cyprus",
        base_rate_pct=Decimal("0"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("17.00"),
        headline_note=(
            "Cyprus does not tax capital gains on securities, so the estimate shows €0. "
            "Dividends may incur 17% SDC unless you qualify as a non-domiciled resident."
        ),
        brackets=[
            TaxBracketSpec(
                label="No CGT on securities",
                rate_pct=Decimal("0"),
                applies_to="Gains on shares/securities (CGT applies to real estate only)",
            ),
            TaxBracketSpec(
                label="SDC on dividends",
                rate_pct=Decimal("17.00"),
                applies_to="Dividends for domiciled residents (non-doms exempt)",
            ),
        ],
    ),
    "EE": CountryTaxProfile(
        code="EE",
        name="Estonia",
        base_rate_pct=Decimal("20.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("0"),
        brackets=[
            TaxBracketSpec(
                label="Personal income tax",
                rate_pct=Decimal("20.00"),
                applies_to="Realised gains (22% from 2025); deferrable via an investment account",
            ),
        ],
    ),
    "FI": CountryTaxProfile(
        code="FI",
        name="Finland",
        base_rate_pct=Decimal("30.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("30.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital income up to €30,000",
                rate_pct=Decimal("30.00"),
                applies_to="Capital gains and dividends",
            ),
            TaxBracketSpec(
                label="Capital income above €30,000",
                rate_pct=Decimal("34.00"),
                applies_to="Capital gains and dividends",
            ),
        ],
    ),
    "GR": CountryTaxProfile(
        code="GR",
        name="Greece",
        base_rate_pct=Decimal("15.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("5.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital gains",
                rate_pct=Decimal("15.00"),
                applies_to="Securities gains (listed-share gains are often exempt)",
            ),
            TaxBracketSpec(
                label="Dividend withholding",
                rate_pct=Decimal("5.00"),
                applies_to="Dividends",
            ),
        ],
    ),
    "IE": CountryTaxProfile(
        code="IE",
        name="Ireland",
        base_rate_pct=Decimal("33.00"),
        annual_allowance_eur=Decimal("1270"),
        dividend_rate_pct=Decimal("40.00"),
        headline_note=(
            "Irish funds and ETFs are taxed under a separate 41% deemed-disposal regime "
            "(every 8 years), not the 33% CGT used in this estimate."
        ),
        brackets=[
            TaxBracketSpec(
                label="Capital Gains Tax",
                rate_pct=Decimal("33.00"),
                applies_to="Capital gains above the €1,270 annual exemption",
            ),
            TaxBracketSpec(
                label="ETF exit tax",
                rate_pct=Decimal("41.00"),
                applies_to="Most funds/ETFs, under 8-year deemed disposal",
            ),
        ],
    ),
    "LV": CountryTaxProfile(
        code="LV",
        name="Latvia",
        base_rate_pct=Decimal("20.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("20.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital income tax",
                rate_pct=Decimal("20.00"),
                applies_to="Capital gains and dividends (dividends exempt if taxed at company level)",
            ),
        ],
    ),
    "LT": CountryTaxProfile(
        code="LT",
        name="Lithuania",
        base_rate_pct=Decimal("15.00"),
        annual_allowance_eur=Decimal("500"),
        dividend_rate_pct=Decimal("15.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital gains / dividends",
                rate_pct=Decimal("15.00"),
                applies_to="Below €500 annual securities-gains exemption is tax-free; 20% above high thresholds",
            ),
        ],
    ),
    "LU": CountryTaxProfile(
        code="LU",
        name="Luxembourg",
        base_rate_pct=Decimal("0"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("15.00"),
        headline_note=(
            "Luxembourg exempts gains on securities held more than 6 months (for "
            "non-substantial holdings), so most buy-and-hold gains are tax-free."
        ),
        brackets=[
            TaxBracketSpec(
                label="Gains on securities held > 6 months",
                rate_pct=Decimal("0"),
                applies_to="Tax-free for non-substantial (<10%) holdings; short-term taxed progressively",
            ),
            TaxBracketSpec(
                label="Dividend withholding",
                rate_pct=Decimal("15.00"),
                applies_to="Dividends (50% exemption then progressive on assessment)",
            ),
        ],
    ),
    "MT": CountryTaxProfile(
        code="MT",
        name="Malta",
        base_rate_pct=Decimal("0"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("0"),
        headline_note=(
            "Malta does not tax gains on transfers of securities, so the estimate shows €0; "
            "dividends are handled under the full-imputation system."
        ),
        brackets=[
            TaxBracketSpec(
                label="No CGT on securities transfers",
                rate_pct=Decimal("0"),
                applies_to="Transfers of shares/securities; dividends under full imputation",
            ),
        ],
    ),
    "SK": CountryTaxProfile(
        code="SK",
        name="Slovakia",
        base_rate_pct=Decimal("19.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("7.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital gains (held < 1 year)",
                rate_pct=Decimal("19.00"),
                applies_to="Exempt if held > 1 year on a regulated market",
            ),
            TaxBracketSpec(
                label="Dividend tax",
                rate_pct=Decimal("7.00"),
                applies_to="Dividends",
            ),
        ],
    ),
    "SI": CountryTaxProfile(
        code="SI",
        name="Slovenia",
        base_rate_pct=Decimal("25.00"),
        annual_allowance_eur=Decimal("0"),
        dividend_rate_pct=Decimal("25.00"),
        brackets=[
            TaxBracketSpec(
                label="Capital gains by holding period",
                rate_pct=Decimal("25.00"),
                applies_to="25% < 5y, 20% 5–10y, 15% 10–15y, 0% > 15y",
            ),
        ],
    ),
}

DEFAULT_PROFILE = COUNTRY_PROFILES["DE"]


def profile_for(country_code: str) -> CountryTaxProfile:
    return COUNTRY_PROFILES.get(country_code.upper(), DEFAULT_PROFILE)


@dataclass(frozen=True)
class TaxOnGains:
    unrealised_gains_eur: Decimal
    taxable_gains_eur: Decimal
    tax_due_eur: Decimal
    after_tax_value_eur: Decimal


def estimate_tax_on_unrealised(
    profile: CountryTaxProfile,
    unrealised_gains_eur: Decimal,
    market_value_eur: Decimal,
    *,
    equity_etf_share_pct: Decimal = Decimal("0"),
) -> TaxOnGains:
    """Apply allowance + partial exemption + base rate. Conservative single-bracket math."""

    if unrealised_gains_eur <= 0:
        return TaxOnGains(
            unrealised_gains_eur=unrealised_gains_eur,
            taxable_gains_eur=Decimal("0"),
            tax_due_eur=Decimal("0"),
            after_tax_value_eur=market_value_eur,
        )

    # Apply equity-ETF partial exemption (e.g. DE Teilfreistellung).
    if profile.equity_etf_partial_exemption_pct > 0 and equity_etf_share_pct > 0:
        exempt_fraction = (
            profile.equity_etf_partial_exemption_pct / Decimal("100")
        ) * (equity_etf_share_pct / Decimal("100"))
        taxable = unrealised_gains_eur * (Decimal("1") - exempt_fraction)
    else:
        taxable = unrealised_gains_eur

    taxable_after_allowance = max(taxable - profile.annual_allowance_eur, Decimal("0"))
    tax_due = (taxable_after_allowance * profile.base_rate_pct / Decimal("100")).quantize(
        Decimal("0.01")
    )
    after_tax = (market_value_eur - tax_due).quantize(Decimal("0.01"))
    return TaxOnGains(
        unrealised_gains_eur=unrealised_gains_eur.quantize(Decimal("0.01")),
        taxable_gains_eur=taxable_after_allowance.quantize(Decimal("0.01")),
        tax_due_eur=tax_due,
        after_tax_value_eur=after_tax,
    )


def estimate_dividend_tax(profile: CountryTaxProfile, annual_dividend_eur: Decimal) -> Decimal:
    if annual_dividend_eur <= 0:
        return Decimal("0")
    return (annual_dividend_eur * profile.dividend_rate_pct / Decimal("100")).quantize(
        Decimal("0.01")
    )


@dataclass(frozen=True)
class CryptoHoldingPeriod:
    """One crypto lot's progress toward the tax-free holding mark. Informational."""

    ticker: str
    quantity: Decimal
    acquired_on: date
    days_held: int
    days_to_tax_free: int  # 0 once the holding period is met
    tax_free: bool


def crypto_holding_periods(
    positions: list,
    *,
    now: datetime,
    holding_period_days: int,
) -> list[CryptoHoldingPeriod]:
    """Per-lot crypto holding-period clock. Pure; sorted soonest-to-tax-free first.

    Purely descriptive — it states where each lot is against the statutory mark.
    It never suggests holding or selling (that would cross into advice).
    """
    out: list[CryptoHoldingPeriod] = []
    for p in positions:
        if getattr(p, "asset_class", None) != "crypto":
            continue
        for lot in getattr(p, "lots", []):
            acquired = lot.purchased_at.date()
            days_held = (now.date() - acquired).days
            remaining = max(0, holding_period_days - days_held)
            out.append(
                CryptoHoldingPeriod(
                    ticker=p.ticker,
                    quantity=lot.quantity,
                    acquired_on=acquired,
                    days_held=days_held,
                    days_to_tax_free=remaining,
                    tax_free=remaining == 0,
                )
            )
    # Lots still on the clock first (soonest to free), then already-free lots.
    return sorted(out, key=lambda h: (h.tax_free, h.days_to_tax_free))
