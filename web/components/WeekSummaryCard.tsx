import { formatSignedEurWhole, formatSignedPct } from "@/lib/moneyFormat";
import type { HoldingSnapshot } from "@/lib/portfolioSnapshot";

export interface WeekSummaryCardProps {
  holdings: HoldingSnapshot[];
  weekChangeEur: number;
  weekChangePct: number;
}

/** Plain-English, two-line recap — describes what happened, never what to do next. */
export function WeekSummaryCard({ holdings, weekChangeEur, weekChangePct }: WeekSummaryCardProps) {
  const leader = holdings.reduce((a, b) => (b.pnlPct > a.pnlPct ? b : a));
  const laggards = holdings.filter((h) => h.pnlPct < 0);

  return (
    <div className="card p-6">
      <p className="label">This week</p>
      <p className="mt-3 text-base leading-relaxed text-ink">
        Your portfolio moved up {formatSignedEurWhole(weekChangeEur)} ({formatSignedPct(weekChangePct)})
        this week, led by {leader.name} at {formatSignedPct(leader.pnlPct)}.
      </p>
      <p className="mt-2 text-base leading-relaxed text-ink-muted">
        {laggards.length > 0
          ? `${laggards.map((h) => h.name).join(", ")} was the only holding to close lower, down ${Math.abs(
              laggards[0].pnlPct,
            ).toFixed(1)}%.`
          : "Every holding closed higher on the week."}
      </p>
    </div>
  );
}
