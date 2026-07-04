"use client";

import Link from "next/link";

import { ConcentrationSummaryCard } from "@/components/ConcentrationSummaryCard";
import { Disclaimer } from "@/components/Disclaimer";
import { HoldingsSnapshotTable } from "@/components/HoldingsSnapshotTable";
import { PortfolioHero } from "@/components/PortfolioHero";
import { WeekSummaryCard } from "@/components/WeekSummaryCard";
import { fetchBriefing, fetchPortfolio } from "@/lib/api";
import { toConcentrationSnapshot, toHoldingSnapshots, toPortfolioSnapshot } from "@/lib/portfolioAdapters";
import { useAsync } from "@/lib/useAsync";

export default function DashboardPage() {
  const { data, loading, error } = useAsync(() =>
    Promise.all([fetchPortfolio(), fetchBriefing()]),
  );

  if (loading) {
    return (
      <div className="space-y-12 fade-up sm:space-y-14">
        <div className="skeleton h-24 w-full" />
        <div className="skeleton h-40 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card border-negative/30 bg-negative-subtle/40 p-5">
        <p className="font-medium text-negative">Couldn&apos;t load your portfolio</p>
        <p className="mt-2 text-sm text-ink">{error}</p>
      </div>
    );
  }

  const [portfolio, briefing] = data;

  if (portfolio.positions.length === 0) {
    return (
      <div className="card space-y-3 p-8 text-center">
        <p className="font-sans text-xl font-semibold text-ink">No holdings yet</p>
        <p className="mx-auto max-w-prose text-sm text-ink-muted">
          Import a broker CSV, or connect a wallet or exchange, to see your dashboard.
        </p>
        <Link href="/upload" className="btn btn-primary mt-2 inline-flex">
          Import a portfolio
        </Link>
      </div>
    );
  }

  const snapshot = toPortfolioSnapshot(portfolio, briefing);
  const holdings = toHoldingSnapshots(portfolio);
  const concentration = toConcentrationSnapshot(portfolio);

  return (
    <div className="space-y-12 fade-up sm:space-y-14">
      <PortfolioHero
        netWorthEur={snapshot.netWorthEur}
        netWorthUsdApprox={snapshot.netWorthUsdApprox}
        weekChangeEur={snapshot.weekChangeEur}
        weekChangePct={snapshot.weekChangePct}
      />

      <section className="grid gap-4 sm:grid-cols-2">
        {concentration ? (
          <ConcentrationSummaryCard concentration={concentration} />
        ) : (
          <div className="card p-6">
            <div className="flex items-center gap-2">
              <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-positive" />
              <p className="label text-positive">Concentration</p>
            </div>
            <p className="mt-3 font-sans text-2xl font-semibold tracking-tight text-ink">Balanced</p>
            <p className="mt-2 text-sm leading-relaxed text-ink-muted">
              No single position is above your concentration thresholds this week.
            </p>
          </div>
        )}
        <WeekSummaryCard
          holdings={holdings}
          weekChangeEur={snapshot.weekChangeEur}
          weekChangePct={snapshot.weekChangePct}
        />
      </section>

      <section className="space-y-4">
        <p className="label">Holdings</p>
        <HoldingsSnapshotTable
          holdings={holdings}
          total={{ netWorthEur: snapshot.netWorthEur, totalPnlPct: snapshot.totalPnlPct }}
        />
      </section>

      <Disclaimer />
    </div>
  );
}
