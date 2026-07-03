// Static Plan-hub content, derived from the same portfolio as the dashboard
// and briefing (see portfolioSnapshot.ts). Figures below are computed from a
// small set of illustrative assumptions rather than hand-typed, so FIRE
// progress, the projection chart, and the tax/rebalance numbers all agree
// with each other and with the real holdings.

import { HOLDINGS_SNAPSHOT, PORTFOLIO_SNAPSHOT } from "@/lib/portfolioSnapshot";
import type {
  DividendResponse,
  DualMoney,
  FireResponse,
  FireTimelinePoint,
  RebalanceResponse,
  TaxSummaryResponse,
} from "@/lib/types";

function eurUsd(eur: number): DualMoney {
  return { eur: eur.toFixed(2), usd: (eur * PORTFOLIO_SNAPSHOT.fxEurUsd).toFixed(2) };
}

// --- FIRE ------------------------------------------------------------------

const REAL_RETURN_PCT = 5;
const ANNUAL_SAVINGS_EUR = 18_000;
const ANNUAL_EXPENSES_EUR = 32_000;
const CURRENT_AGE = 34;
const HORIZON_YEARS = 40;

const LEAN_FIRE_EUR = 550_000;
const COAST_FIRE_EUR = 210_000;
const FULL_FIRE_EUR = 800_000;
const FAT_FIRE_EUR = 1_100_000;

function projectedNetWorth(yearOffset: number): number {
  const r = REAL_RETURN_PCT / 100;
  const growth = Math.pow(1 + r, yearOffset);
  return PORTFOLIO_SNAPSHOT.netWorthEur * growth + ANNUAL_SAVINGS_EUR * ((growth - 1) / r);
}

const FIRE_TIMELINE: FireTimelinePoint[] = Array.from({ length: HORIZON_YEARS + 1 }, (_, yearOffset) => {
  const value = projectedNetWorth(yearOffset);
  return {
    year_offset: yearOffset,
    age: CURRENT_AGE + yearOffset,
    projected_net_worth_eur: value.toFixed(2),
    is_coast_fire: value >= COAST_FIRE_EUR,
    is_full_fire: value >= FULL_FIRE_EUR,
  };
});

/** Fractional year a target is crossed, linearly interpolated between the two bracketing points. */
function yearsToReach(target: number): number | null {
  for (let i = 0; i < FIRE_TIMELINE.length; i++) {
    const value = Number(FIRE_TIMELINE[i].projected_net_worth_eur);
    if (value >= target) {
      if (i === 0) return 0;
      const prev = Number(FIRE_TIMELINE[i - 1].projected_net_worth_eur);
      const frac = (target - prev) / (value - prev);
      return FIRE_TIMELINE[i - 1].year_offset + frac;
    }
  }
  return null;
}

export const FIRE_SNAPSHOT: FireResponse = {
  annual_expenses_eur: ANNUAL_EXPENSES_EUR.toFixed(2),
  annual_savings_eur: ANNUAL_SAVINGS_EUR.toFixed(2),
  expected_real_return_pct: REAL_RETURN_PCT.toFixed(2),
  safe_withdrawal_rate_pct: "4.00",
  current_net_worth: eurUsd(PORTFOLIO_SNAPSHOT.netWorthEur),
  full_fire_number: eurUsd(FULL_FIRE_EUR),
  coast_fire_number: eurUsd(COAST_FIRE_EUR),
  lean_fire_number: eurUsd(LEAN_FIRE_EUR),
  fat_fire_number: eurUsd(FAT_FIRE_EUR),
  full_fire_progress_pct: ((PORTFOLIO_SNAPSHOT.netWorthEur / FULL_FIRE_EUR) * 100).toFixed(1),
  coast_fire_progress_pct: ((PORTFOLIO_SNAPSHOT.netWorthEur / COAST_FIRE_EUR) * 100).toFixed(1),
  years_to_full_fire: yearsToReach(FULL_FIRE_EUR)?.toFixed(1) ?? null,
  years_to_coast_fire: yearsToReach(COAST_FIRE_EUR)?.toFixed(1) ?? null,
  timeline: FIRE_TIMELINE,
  notes: [
    "Assumes a constant 5% real return and steady €18,000 annual savings — markets don't move in a straight line.",
    "Coast FIRE is the point where growth alone, with no further saving, reaches Full FIRE by the projection above.",
  ],
};

// --- Dividend ----------------------------------------------------------------

// VWCE and SXR8 are accumulating share classes — no cash dividend, by design
// (common in the EU to defer dividend tax). Only ASML, a real dividend payer,
// contributes here.
const asml = HOLDINGS_SNAPSHOT.find((h) => h.ticker === "ASML")!;
const ASML_YIELD_PCT = 0.9;
const asmlAnnualDividend = asml.valueEur * (ASML_YIELD_PCT / 100);

export const DIVIDEND_SNAPSHOT: DividendResponse = {
  total_annual: eurUsd(asmlAnnualDividend),
  total_monthly: eurUsd(asmlAnnualDividend / 12),
  weighted_yield_pct: ((asmlAnnualDividend / PORTFOLIO_SNAPSHOT.netWorthEur) * 100).toFixed(2),
  forward_12m_growth_pct: "6.50",
  positions: [
    {
      ticker: asml.ticker,
      asset_class: "stock",
      market_value: eurUsd(asml.valueEur),
      yield_pct: ASML_YIELD_PCT.toFixed(2),
      annual_dividend: eurUsd(asmlAnnualDividend),
      monthly_dividend: eurUsd(asmlAnnualDividend / 12),
      source: "known",
    },
  ],
  notes: [
    "VWCE and SXR8 are accumulating share classes — dividends are reinvested internally, not paid out as cash.",
    "Estimated from ASML's most recently declared dividend; actual payouts can vary year to year.",
  ],
};

// --- Rebalance ---------------------------------------------------------------

const TOTAL_EUR = PORTFOLIO_SNAPSHOT.netWorthEur;
const vwce = HOLDINGS_SNAPSHOT.find((h) => h.ticker === "VWCE")!;
const sxr8 = HOLDINGS_SNAPSHOT.find((h) => h.ticker === "SXR8")!;
const btc = HOLDINGS_SNAPSHOT.find((h) => h.ticker === "BTC")!;

const CURRENT_ETF_EUR = vwce.valueEur + sxr8.valueEur;
const CURRENT_STOCK_EUR = asml.valueEur;
const CURRENT_CRYPTO_EUR = btc.valueEur;
const CURRENT_CASH_EUR = 0;

const TARGET_PCT: Record<string, number> = { etf: 65, stock: 18, crypto: 12, cash: 5 };

function rebalanceLeg(assetClass: string, currentEur: number) {
  const currentPct = (currentEur / TOTAL_EUR) * 100;
  const targetPct = TARGET_PCT[assetClass];
  const targetEur = TOTAL_EUR * (targetPct / 100);
  const deltaEur = targetEur - currentEur;
  const driftPct = currentPct - targetPct;
  const action: "buy" | "sell" | "hold" = driftPct > 1 ? "sell" : driftPct < -1 ? "buy" : "hold";
  return {
    asset_class: assetClass,
    current_pct: currentPct.toFixed(2),
    target_pct: targetPct.toFixed(2),
    drift_pct: driftPct.toFixed(2),
    current_value: eurUsd(currentEur),
    target_value: eurUsd(targetEur),
    delta: eurUsd(deltaEur),
    action,
  };
}

const REBALANCE_LEGS = [
  rebalanceLeg("etf", CURRENT_ETF_EUR),
  rebalanceLeg("stock", CURRENT_STOCK_EUR),
  rebalanceLeg("crypto", CURRENT_CRYPTO_EUR),
  rebalanceLeg("cash", CURRENT_CASH_EUR),
];

const DRIFT_SCORE = REBALANCE_LEGS.reduce((sum, leg) => sum + Math.abs(Number(leg.drift_pct)), 0) / 2;

export const REBALANCE_SNAPSHOT: RebalanceResponse = {
  total_value: eurUsd(TOTAL_EUR),
  drift_score: DRIFT_SCORE.toFixed(2),
  needs_rebalance: REBALANCE_LEGS.some((leg) => Math.abs(Number(leg.drift_pct)) > 5),
  legs: REBALANCE_LEGS,
  method: "5-percentage-point band per asset class",
  notes: [
    "ETFs are running hot relative to target, mostly from this year's equity gains rather than new buying.",
    "These are portfolio-shape observations, not instructions — whether and when to act is yours to decide.",
  ],
};

// --- Tax (illustrative: Germany's flat Abgeltungsteuer) ----------------------

const DE_FLAT_RATE_PCT = 26.375; // 25% + 5.5% solidarity surcharge on the tax, not the gain
const DE_ALLOWANCE_EUR = 1_000; // Sparerpauschbetrag, single filer

function costBasis(h: (typeof HOLDINGS_SNAPSHOT)[number]): number {
  return h.valueEur / (1 + h.pnlPct / 100);
}

const UNREALISED_GAIN_EUR = HOLDINGS_SNAPSHOT.reduce((sum, h) => sum + (h.valueEur - costBasis(h)), 0);
const TAXABLE_GAIN_EUR = Math.max(0, UNREALISED_GAIN_EUR - DE_ALLOWANCE_EUR);
const TAX_IF_REALISED_EUR = TAXABLE_GAIN_EUR * (DE_FLAT_RATE_PCT / 100);
const DIVIDEND_TAX_EUR = asmlAnnualDividend * (DE_FLAT_RATE_PCT / 100);

// BTC's FIFO acquisition date, for the crypto holding-period clock below.
const BTC_ACQUIRED_ON = "2025-10-15";
const CRYPTO_TAX_FREE_AFTER_DAYS = 365; // Germany's private-sale exemption for crypto held > 1 year

function daysBetween(fromIso: string, toIso: string): number {
  const ms = new Date(toIso).getTime() - new Date(fromIso).getTime();
  return Math.round(ms / (1000 * 60 * 60 * 24));
}

const BTC_DAYS_HELD = daysBetween(BTC_ACQUIRED_ON, PORTFOLIO_SNAPSHOT.asOfDate);

export const TAX_SNAPSHOT: TaxSummaryResponse = {
  country: "DE",
  country_name: "Germany",
  base_rate_pct: DE_FLAT_RATE_PCT.toFixed(3),
  annual_allowance_eur: DE_ALLOWANCE_EUR.toFixed(2),
  brackets: [
    {
      label: "Capital gains tax (Abgeltungsteuer)",
      rate_pct: DE_FLAT_RATE_PCT.toFixed(3),
      applies_to: "Gains above your €1,000 annual allowance",
    },
  ],
  unrealised_gains: eurUsd(UNREALISED_GAIN_EUR),
  estimated_tax_if_realised: eurUsd(TAX_IF_REALISED_EUR),
  after_tax_value_if_realised: eurUsd(PORTFOLIO_SNAPSHOT.netWorthEur - TAX_IF_REALISED_EUR),
  annual_dividend_estimate: eurUsd(asmlAnnualDividend),
  estimated_dividend_tax: eurUsd(DIVIDEND_TAX_EUR),
  crypto_tax_free_after_days: CRYPTO_TAX_FREE_AFTER_DAYS,
  crypto_holding_periods: [
    {
      ticker: btc.ticker,
      quantity: "0.32000000",
      acquired_on: BTC_ACQUIRED_ON,
      days_held: BTC_DAYS_HELD,
      days_to_tax_free: Math.max(0, CRYPTO_TAX_FREE_AFTER_DAYS - BTC_DAYS_HELD),
      tax_free: BTC_DAYS_HELD >= CRYPTO_TAX_FREE_AFTER_DAYS,
    },
  ],
  notes: [
    "Capital gains are tracked first-in-first-out per holding.",
    "The flat rate already includes the 5.5% solidarity surcharge; church tax, if registered, adds more on top.",
  ],
  disclaimer:
    "Tax rules vary by residency and change often. This is a planning estimate, not tax advice — confirm with a professional before filing.",
};
