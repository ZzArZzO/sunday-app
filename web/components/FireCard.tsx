import Link from "next/link";

import type { FireResponse } from "@/lib/types";
import { formatDual, formatEur, formatPct } from "@/lib/format";

interface FireCardProps {
  fire: FireResponse;
  href?: string;
}

/**
 * Compact FIRE summary for the dashboard. Shows progress to full FIRE, years
 * remaining, and the four canonical FIRE numbers (Lean / Coast / Full / Fat).
 * Drills into the full /fire planner view.
 */
export function FireCard({ fire, href = "/fire" }: FireCardProps) {
  const progress = Number(fire.full_fire_progress_pct);
  const years = fire.years_to_full_fire ? Number(fire.years_to_full_fire) : null;
  const cappedProgress = Math.min(progress, 100);

  return (
    <article className="card p-5 sm:p-6">
      <header className="flex items-baseline justify-between gap-3">
        <p className="label">Financial independence</p>
        <Link href={href} className="text-xs font-medium text-accent hover:underline">
          Open planner →
        </Link>
      </header>

      <div className="mt-4 flex items-baseline gap-3">
        <p className="font-mono text-4xl font-semibold tabular-nums text-ink sm:text-5xl">
          {progress.toFixed(1)}%
        </p>
        <p className="text-sm text-ink-muted">
          {years === null
            ? "Set savings to estimate"
            : years <= 0
              ? "Reached — congratulations"
              : `${years.toFixed(1)} yrs to full FIRE`}
        </p>
      </div>

      <div
        className="mt-4 h-2 w-full overflow-hidden rounded-full bg-surface-2"
        role="progressbar"
        aria-valuenow={cappedProgress}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full bg-accent transition-all duration-500"
          style={{ width: `${cappedProgress}%` }}
        />
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Milestone label="Lean" value={formatDual(fire.lean_fire_number).split(" / ")[0]} />
        <Milestone label="Coast" value={formatDual(fire.coast_fire_number).split(" / ")[0]} />
        <Milestone label="Full" value={formatDual(fire.full_fire_number).split(" / ")[0]} />
        <Milestone label="Fat" value={formatDual(fire.fat_fire_number).split(" / ")[0]} />
      </dl>

      <p className="mt-4 text-xs text-ink-subtle">
        Current net worth {formatDual(fire.current_net_worth)} · SWR{" "}
        {formatPct(fire.safe_withdrawal_rate_pct)} · Real return{" "}
        {formatPct(fire.expected_real_return_pct)}
      </p>
    </article>
  );
}

function Milestone({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-rule bg-surface-2/40 p-3">
      <dt className="label">{label}</dt>
      <dd className="mt-1 font-mono text-sm tabular-nums text-ink">{value}</dd>
    </div>
  );
}

/**
 * Helper to avoid importing formatEur in callers when they only have a Decimal-as-string.
 */
export function FireMilestone({ label, eur }: { label: string; eur: string }) {
  return <Milestone label={label} value={formatEur(eur)} />;
}
