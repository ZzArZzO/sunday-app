// Maps the live API's PortfolioResponse/BriefingResponse (money as EUR/USD
// string pairs, percentages as strings, per-ticker concentration flags) into
// the plain-number presentation shapes the dashboard components expect.
// PortfolioResponse has no week-over-week figure of its own — that only
// exists on the briefing (it's computed from snapshot history) — so the
// dashboard fetches both and this adapter combines them.

import type { ConcentrationSnapshot, HoldingSnapshot, PortfolioSnapshot } from "@/lib/portfolioSnapshot";
import type { BriefingResponse, PortfolioResponse } from "@/lib/types";

function pctReturn(gainEur: number, costEur: number): number {
  return costEur > 0 ? (gainEur / costEur) * 100 : 0;
}

export function toPortfolioSnapshot(
  portfolio: PortfolioResponse,
  briefing: BriefingResponse,
): PortfolioSnapshot {
  return {
    netWorthEur: Number(portfolio.total_value.eur),
    netWorthUsdApprox: Number(portfolio.total_value.usd),
    weekChangeEur: Number(briefing.wow_delta.eur),
    weekChangePct: Number(briefing.wow_delta_pct),
    totalPnlPct: pctReturn(Number(portfolio.total_pnl.eur), Number(portfolio.total_cost.eur)),
    fxEurUsd: Number(portfolio.fx_eur_usd),
    asOfDate: portfolio.as_of,
  };
}

export function toHoldingSnapshots(portfolio: PortfolioResponse): HoldingSnapshot[] {
  return portfolio.positions.map((p) => ({
    ticker: p.ticker,
    // The live API doesn't carry a human-readable instrument name, only the
    // ticker — real names (e.g. "Vanguard FTSE All-World") would need a
    // separate reference-data lookup, out of scope here.
    name: p.ticker,
    valueEur: Number(p.market_value.eur),
    pnlPct: pctReturn(Number(p.unrealised_pnl.eur), Number(p.cost_basis.eur)),
    weightPct: Number(p.weight_pct),
  }));
}

/**
 * `portfolio.concentration` only ever contains positions already over a
 * warn/alert threshold (see api/app/services/concentration.py) — never a
 * "0% over" placeholder — so an empty list genuinely means no concern this
 * week. Returns the single highest-weight flagged position, or null.
 */
export function toConcentrationSnapshot(portfolio: PortfolioResponse): ConcentrationSnapshot | null {
  if (portfolio.concentration.length === 0) return null;
  const top = portfolio.concentration.reduce((a, b) => (Number(b.weight_pct) > Number(a.weight_pct) ? b : a));
  return {
    label: top.ticker,
    weightPct: Number(top.weight_pct),
    thresholdPct: Number(top.threshold_pct),
  };
}
