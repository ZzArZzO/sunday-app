import { Disclaimer } from "@/components/Disclaimer";
import { FireTimeline } from "@/components/FireTimeline";
import { fetchFire } from "@/lib/api";
import { formatDual, formatEur, formatPct } from "@/lib/format";

export const dynamic = "force-dynamic";
export const metadata = {
  title: "FIRE planner — Sunday",
  description: "Financial independence projection for your portfolio.",
};

export default async function FirePage() {
  let fire;
  try {
    fire = await fetchFire();
  } catch (err) {
    return (
      <div className="card border-negative/30 bg-negative-subtle/40 p-5">
        <p className="font-medium text-negative">Couldn&apos;t load FIRE planner</p>
        <p className="mt-2 text-sm text-ink">
          {err instanceof Error ? err.message : String(err)}
        </p>
      </div>
    );
  }

  const progress = Number(fire.full_fire_progress_pct);
  const cappedProgress = Math.min(progress, 100);
  const yearsFull = fire.years_to_full_fire ? Number(fire.years_to_full_fire) : null;
  const yearsCoast = fire.years_to_coast_fire ? Number(fire.years_to_coast_fire) : null;

  return (
    <article className="space-y-10 fade-up sm:space-y-12">
      <header className="space-y-3">
        <p className="label">Financial independence · planner</p>
        <h1 className="font-sans text-4xl font-semibold leading-tight tracking-tighter text-ink sm:text-5xl">
          {progress.toFixed(1)}% of the way to full FIRE.
        </h1>
        <p className="max-w-prose text-base leading-relaxed text-ink-muted">
          Based on your current net worth of{" "}
          <span className="font-mono text-ink">{formatDual(fire.current_net_worth)}</span>,
          a real return assumption of{" "}
          <span className="font-mono text-ink">{formatPct(fire.expected_real_return_pct)}</span>,
          and a {formatPct(fire.safe_withdrawal_rate_pct)} safe withdrawal rate.
        </p>
      </header>

      <section className="card p-6 sm:p-8">
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <div>
            <p className="label">Progress to full FIRE</p>
            <p className="mt-2 font-mono text-5xl font-semibold tabular-nums text-ink">
              {progress.toFixed(1)}%
            </p>
          </div>
          <div className="text-right">
            <p className="label">Years remaining</p>
            <p className="mt-2 font-mono text-3xl tabular-nums text-ink">
              {yearsFull === null ? "—" : yearsFull <= 0 ? "Reached" : yearsFull.toFixed(1)}
            </p>
            {yearsCoast !== null && yearsCoast > 0 ? (
              <p className="mt-1 text-xs text-ink-subtle">
                Coast FIRE in {yearsCoast.toFixed(1)} years
              </p>
            ) : null}
          </div>
        </div>

        <div
          className="mt-6 h-3 w-full overflow-hidden rounded-full bg-surface-2"
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
      </section>

      <FireTimeline
        points={fire.timeline}
        fullFireEur={fire.full_fire_number.eur}
        coastFireEur={fire.coast_fire_number.eur}
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MilestoneCard
          name="Lean FIRE"
          subtitle="Bare-essentials lifestyle"
          eur={fire.lean_fire_number.eur}
          accent={false}
        />
        <MilestoneCard
          name="Coast FIRE"
          subtitle="No further saving needed"
          eur={fire.coast_fire_number.eur}
          accent={false}
        />
        <MilestoneCard
          name="Full FIRE"
          subtitle="The 4% rule baseline"
          eur={fire.full_fire_number.eur}
          accent
        />
        <MilestoneCard
          name="Fat FIRE"
          subtitle="Comfortable + buffer"
          eur={fire.fat_fire_number.eur}
          accent={false}
        />
      </section>

      <section className="card p-6 sm:p-8">
        <p className="label">Inputs</p>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Input
            label="Annual expenses"
            value={fire.annual_expenses_eur ? formatEur(fire.annual_expenses_eur) : "—"}
            note={fire.annual_expenses_eur ? null : "Set on your profile"}
          />
          <Input
            label="Annual savings"
            value={fire.annual_savings_eur ? formatEur(fire.annual_savings_eur) : "—"}
            note={fire.annual_savings_eur ? null : "Set on your profile"}
          />
          <Input
            label="Real return"
            value={formatPct(fire.expected_real_return_pct)}
            note="After inflation"
          />
          <Input
            label="Withdrawal rate"
            value={formatPct(fire.safe_withdrawal_rate_pct)}
            note="The 4% rule by default"
          />
        </dl>
        {fire.notes.length > 0 ? (
          <ul className="mt-4 space-y-1 text-xs text-ink-subtle">
            {fire.notes.map((note, idx) => (
              <li key={idx}>· {note}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <Disclaimer extra="FIRE projections assume constant real return and savings. Markets vary; figures are a planning aid, not a guarantee." />
    </article>
  );
}

function MilestoneCard({
  name,
  subtitle,
  eur,
  accent,
}: {
  name: string;
  subtitle: string;
  eur: string;
  accent: boolean;
}) {
  return (
    <div
      className={`card p-5 ${accent ? "border-accent/40 bg-accent-subtle/30" : ""}`}
    >
      <p className="label">{name}</p>
      <p className="mt-3 font-mono text-2xl font-semibold tabular-nums text-ink">
        {formatEur(eur)}
      </p>
      <p className="mt-1 text-xs text-ink-subtle">{subtitle}</p>
    </div>
  );
}

function Input({ label, value, note }: { label: string; value: string; note: string | null }) {
  return (
    <div>
      <dt className="label">{label}</dt>
      <dd className="mt-1 font-mono text-lg tabular-nums text-ink">{value}</dd>
      {note ? <p className="mt-1 text-xs text-ink-subtle">{note}</p> : null}
    </div>
  );
}
