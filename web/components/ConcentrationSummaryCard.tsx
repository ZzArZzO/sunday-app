import type { ConcentrationSnapshot } from "@/lib/portfolioSnapshot";

export interface ConcentrationSummaryCardProps {
  concentration: ConcentrationSnapshot;
}

/**
 * Describes concentration risk without prescribing action. Uses the `warn`
 * token (amber) rather than the gain/loss blue/orange pair — this isn't a
 * loss, it's a portfolio-shape note, and reusing loss-orange here would blur
 * the one signal that's supposed to mean "down".
 */
export function ConcentrationSummaryCard({ concentration }: ConcentrationSummaryCardProps) {
  const over = concentration.weightPct - concentration.thresholdPct;

  return (
    <div className="card p-6">
      <div className="flex items-center gap-2">
        <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-warn" />
        <p className="label text-warn">Concentration</p>
      </div>
      <p className="mt-3 font-sans text-2xl font-semibold tracking-tight text-ink">
        {concentration.label} · {concentration.weightPct}%
      </p>
      <p className="mt-2 text-sm leading-relaxed text-ink-muted">
        That&apos;s {over} percentage points above your {concentration.thresholdPct}% guideline. Noted here
        for awareness — Sunday describes your portfolio, it doesn&apos;t tell you what to do with it.
      </p>
    </div>
  );
}
