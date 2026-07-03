// Static content shared across screen redesigns (dashboard, briefing). Numbers
// are illustrative product-brief data, not fetched — this module exists so
// every screen renders the same underlying portfolio instead of each
// inlining its own literals.

export interface HoldingSnapshot {
  ticker: string;
  name: string;
  valueEur: number;
  pnlPct: number;
  weightPct: number;
}

export interface PortfolioSnapshot {
  netWorthEur: number;
  netWorthUsdApprox: number;
  weekChangeEur: number;
  weekChangePct: number;
  totalPnlPct: number;
  fxEurUsd: number;
  /** ISO date this snapshot represents — matches the briefing's dateline. */
  asOfDate: string;
}

export interface ConcentrationSnapshot {
  label: string;
  weightPct: number;
  thresholdPct: number;
}

export const PORTFOLIO_SNAPSHOT: PortfolioSnapshot = {
  netWorthEur: 142_580,
  netWorthUsdApprox: 154_200,
  weekChangeEur: 3_340,
  weekChangePct: 2.4,
  totalPnlPct: 6.1,
  fxEurUsd: 1.0842,
  asOfDate: "2026-06-30",
};

export const HOLDINGS_SNAPSHOT: HoldingSnapshot[] = [
  { ticker: "VWCE", name: "Vanguard FTSE All-World", valueEur: 61_240, pnlPct: 8.2, weightPct: 43 },
  { ticker: "SXR8", name: "iShares Core S&P 500", valueEur: 38_900, pnlPct: 5.1, weightPct: 27 },
  { ticker: "ASML", name: "ASML Holding", valueEur: 23_540, pnlPct: -2.3, weightPct: 17 },
  { ticker: "BTC", name: "Bitcoin", valueEur: 18_900, pnlPct: 12.4, weightPct: 13 },
];

export const CONCENTRATION_SNAPSHOT: ConcentrationSnapshot = {
  label: "Tech",
  weightPct: 41,
  thresholdPct: 35,
};
