import { ConcentrationSummaryCard } from "@/components/ConcentrationSummaryCard";
import { Disclaimer } from "@/components/Disclaimer";
import { HoldingsSnapshotTable } from "@/components/HoldingsSnapshotTable";
import { PortfolioHero } from "@/components/PortfolioHero";
import { WeekSummaryCard } from "@/components/WeekSummaryCard";
import { CONCENTRATION_SNAPSHOT, HOLDINGS_SNAPSHOT, PORTFOLIO_SNAPSHOT } from "@/lib/portfolioSnapshot";

export default function DashboardPage() {
  return (
    <div className="space-y-12 fade-up sm:space-y-14">
      <PortfolioHero
        netWorthEur={PORTFOLIO_SNAPSHOT.netWorthEur}
        netWorthUsdApprox={PORTFOLIO_SNAPSHOT.netWorthUsdApprox}
        weekChangeEur={PORTFOLIO_SNAPSHOT.weekChangeEur}
        weekChangePct={PORTFOLIO_SNAPSHOT.weekChangePct}
      />

      <section className="grid gap-4 sm:grid-cols-2">
        <ConcentrationSummaryCard concentration={CONCENTRATION_SNAPSHOT} />
        <WeekSummaryCard
          holdings={HOLDINGS_SNAPSHOT}
          weekChangeEur={PORTFOLIO_SNAPSHOT.weekChangeEur}
          weekChangePct={PORTFOLIO_SNAPSHOT.weekChangePct}
        />
      </section>

      <section className="space-y-4">
        <p className="label">Holdings</p>
        <HoldingsSnapshotTable
          holdings={HOLDINGS_SNAPSHOT}
          total={{ netWorthEur: PORTFOLIO_SNAPSHOT.netWorthEur, totalPnlPct: PORTFOLIO_SNAPSHOT.totalPnlPct }}
        />
      </section>

      <Disclaimer />
    </div>
  );
}
