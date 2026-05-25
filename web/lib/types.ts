// Mirrors api/app/schemas. Kept in sync manually until we wire OpenAPI codegen.

export type DualMoney = {
  eur: string;
  usd: string;
};

export type PositionView = {
  id: number;
  ticker: string;
  isin: string | null;
  asset_class: string;
  sector: string | null;
  region: string | null;
  currency: string;
  quantity: string;
  avg_cost_eur: string;
  last_price_eur: string | null;
  market_value: DualMoney;
  cost_basis: DualMoney;
  unrealised_pnl: DualMoney;
  weight_pct: string;
};

export type ConcentrationItem = {
  ticker: string;
  weight_pct: string;
  threshold_pct: string;
  severity: "info" | "warning" | "alert";
};

export type PortfolioResponse = {
  portfolio_id: number;
  as_of: string;
  fx_eur_usd: string;
  total_value: DualMoney;
  total_cost: DualMoney;
  total_pnl: DualMoney;
  positions: PositionView[];
  concentration: ConcentrationItem[];
  asset_class_split: Record<string, string>;
};

export type BriefingSection = {
  kind: string;
  title: string;
  body_markdown: string;
  data: Record<string, unknown> | null;
};

export type BriefingResponse = {
  portfolio_id: number;
  week_of: string;
  generated_at: string;
  fx_eur_usd: string;
  net_worth: DualMoney;
  wow_delta: DualMoney;
  wow_delta_pct: string;
  sections: BriefingSection[];
  concentration_alerts: ConcentrationItem[];
  disclaimers: string[];
};

export type IngestResult = {
  rows_read: number;
  positions_created: number;
  positions_updated: number;
  lots_created: number;
  warnings: string[];
};

// --- FIRE ----------------------------------------------------------------

export type FireTimelinePoint = {
  year_offset: number;
  age: number | null;
  projected_net_worth_eur: string;
  is_coast_fire: boolean;
  is_full_fire: boolean;
};

export type FireResponse = {
  annual_expenses_eur: string | null;
  annual_savings_eur: string | null;
  expected_real_return_pct: string;
  safe_withdrawal_rate_pct: string;
  current_net_worth: DualMoney;
  full_fire_number: DualMoney;
  coast_fire_number: DualMoney;
  lean_fire_number: DualMoney;
  fat_fire_number: DualMoney;
  full_fire_progress_pct: string;
  coast_fire_progress_pct: string;
  years_to_full_fire: string | null;
  years_to_coast_fire: string | null;
  timeline: FireTimelinePoint[];
  notes: string[];
};

// --- Dividend ------------------------------------------------------------

export type DividendPositionView = {
  ticker: string;
  asset_class: string;
  market_value: DualMoney;
  yield_pct: string;
  annual_dividend: DualMoney;
  monthly_dividend: DualMoney;
  source: "estimate" | "known";
};

export type DividendResponse = {
  total_annual: DualMoney;
  total_monthly: DualMoney;
  weighted_yield_pct: string;
  forward_12m_growth_pct: string;
  positions: DividendPositionView[];
  notes: string[];
};

// --- Tax -----------------------------------------------------------------

export type TaxBracket = {
  label: string;
  rate_pct: string;
  applies_to: string;
};

export type TaxSummaryResponse = {
  country: string;
  country_name: string;
  base_rate_pct: string;
  annual_allowance_eur: string;
  brackets: TaxBracket[];
  unrealised_gains: DualMoney;
  estimated_tax_if_realised: DualMoney;
  after_tax_value_if_realised: DualMoney;
  annual_dividend_estimate: DualMoney;
  estimated_dividend_tax: DualMoney;
  notes: string[];
  disclaimer: string;
};

// --- Rebalance -----------------------------------------------------------

export type RebalanceLeg = {
  asset_class: string;
  current_pct: string;
  target_pct: string;
  drift_pct: string;
  current_value: DualMoney;
  target_value: DualMoney;
  delta: DualMoney;
  action: "buy" | "sell" | "hold";
};

export type RebalanceResponse = {
  total_value: DualMoney;
  drift_score: string;
  needs_rebalance: boolean;
  legs: RebalanceLeg[];
  method: string;
  notes: string[];
};
