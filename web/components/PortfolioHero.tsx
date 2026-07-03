"use client";

import Link from "next/link";
import { useState } from "react";

import { GainLossTag } from "@/components/GainLossTag";
import { refreshPrices } from "@/lib/api";
import { formatEurWhole, formatSignedEurWhole, formatSignedPct, formatUsdApprox } from "@/lib/moneyFormat";

export interface PortfolioHeroProps {
  netWorthEur: number;
  netWorthUsdApprox: number;
  weekChangeEur: number;
  weekChangePct: number;
}

type RefreshState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done"; priced: number; total: number }
  | { kind: "error"; message: string };

/**
 * The screen's single focal point: net worth, its quiet USD reference, and
 * this week's move. Two actions sit directly beneath it so the next step is
 * never more than a glance away.
 */
export function PortfolioHero({
  netWorthEur,
  netWorthUsdApprox,
  weekChangeEur,
  weekChangePct,
}: PortfolioHeroProps) {
  const [refresh, setRefresh] = useState<RefreshState>({ kind: "idle" });

  async function handleRefresh() {
    setRefresh({ kind: "loading" });
    try {
      const res = await refreshPrices();
      setRefresh({ kind: "done", priced: res.priced, total: res.priced + res.unpriced });
    } catch (err) {
      setRefresh({ kind: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  return (
    <section className="space-y-6">
      <p className="label">Net worth</p>

      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h1 className="font-sans text-5xl font-semibold leading-none tracking-tighter text-ink sm:text-6xl">
          {formatEurWhole(netWorthEur)}
        </h1>
        <span className="font-mono text-lg tabular-nums text-ink-subtle">
          {formatUsdApprox(netWorthUsdApprox)}
        </span>
      </div>

      <GainLossTag
        value={weekChangePct}
        size="lg"
        label={`${formatSignedEurWhole(weekChangeEur)} · ${formatSignedPct(weekChangePct)} this week`}
      />

      <div className="flex flex-wrap items-center gap-3 pt-2">
        <Link href="/briefing" className="btn btn-primary">
          See this week&apos;s briefing
        </Link>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={refresh.kind === "loading"}
          className="btn btn-ghost"
        >
          {refresh.kind === "loading" ? "Refreshing…" : "Refresh prices"}
        </button>
        <span aria-live="polite" className="text-sm text-ink-subtle">
          {refresh.kind === "done" ? `Priced ${refresh.priced}/${refresh.total} holdings` : null}
          {refresh.kind === "error" ? <span className="text-negative">{refresh.message}</span> : null}
        </span>
      </div>
    </section>
  );
}
