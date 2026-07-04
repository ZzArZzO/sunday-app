export interface BriefingMastheadProps {
  /** ISO date, e.g. "2026-07-04" — the briefing's week_of field. */
  weekOf: string;
  readMinutes: number;
}

/**
 * The letter's own masthead — distinct from the app's persistent top nav.
 * No issue number: the backend doesn't track a per-user edition count, and
 * inventing one here would just be a fake-looking number, not a real one.
 */
export function BriefingMasthead({ weekOf, readMinutes }: BriefingMastheadProps) {
  const dateline = new Date(weekOf).toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <header className="space-y-4 border-b border-rule pb-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <span className="font-sans text-base font-semibold tracking-tight text-ink">Sunday</span>
        <p className="font-mono text-xs tabular-nums text-ink-subtle">{readMinutes} min read</p>
      </div>
      <p className="text-sm text-ink-subtle">{dateline}</p>
    </header>
  );
}
