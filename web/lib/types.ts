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
