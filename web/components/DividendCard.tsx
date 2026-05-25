import type { DividendResponse } from "@/lib/types";
import { formatDual, formatEur, formatPct } from "@/lib/format";

interface DividendCardProps {
  dividend: DividendResponse;
}

export function DividendCard({ dividend }: DividendCardProps) {
  const top = dividend.positions.slice(0, 5);

  return (
    <article className="card p-5 sm:p-6">
      <header className="flex items-baseline justify-between gap-3">
        <p className="label">Dividend income</p>
        <p className="font-mono text-xs text-ink-subtle">
          Yield {formatPct(dividend.weighted_yield_pct)}
        </p>
      </header>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Tile
          label="Annual"
          value={formatDual(dividend.total_annual).split(" / ")[0]}
          sub={`${formatEur(dividend.total_annual.eur)} / yr`}
          aria="Forward 12-month dividend income"
        />
        <Tile
          label="Monthly avg"
          value={formatDual(dividend.total_monthly).split(" / ")[0]}
          sub={`${formatEur(dividend.total_monthly.eur)} / mo`}
          aria="Average monthly dividend income"
        />
      </div>

      {top.length > 0 ? (
        <div className="mt-5 space-y-2">
          <p className="label">Top contributors</p>
          <ul className="divide-y divide-rule">
            {top.map((line) => (
              <li
                key={line.ticker}
                className="flex items-center justify-between py-2 text-sm"
              >
                <span className="flex items-center gap-2">
                  <span className="font-semibold text-ink">{line.ticker}</span>
                  <SourceBadge source={line.source} />
                </span>
                <span className="flex items-baseline gap-3 font-mono tabular-nums text-ink-muted">
                  <span>{formatPct(line.yield_pct)}</span>
                  <span className="text-ink">{formatEur(line.annual_dividend.eur)}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-4 text-sm text-ink-muted">
          No dividend-paying positions detected yet.
        </p>
      )}

      {dividend.notes.length > 0 ? (
        <p className="mt-4 text-xs text-ink-subtle">{dividend.notes.join(" · ")}</p>
      ) : null}
    </article>
  );
}

function Tile({
  label,
  value,
  sub,
  aria,
}: {
  label: string;
  value: string;
  sub: string;
  aria: string;
}) {
  return (
    <div
      className="rounded-md border border-rule bg-surface-2/40 p-4"
      aria-label={aria}
    >
      <p className="label">{label}</p>
      <p className="mt-1 font-mono text-2xl tabular-nums text-ink">{value}</p>
      <p className="mt-1 text-xs text-ink-subtle">{sub}</p>
    </div>
  );
}

function SourceBadge({ source }: { source: "estimate" | "known" }) {
  const isKnown = source === "known";
  return (
    <span
      className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
        isKnown
          ? "border-positive/30 bg-positive-subtle/40 text-positive"
          : "border-rule bg-surface-2 text-ink-subtle"
      }`}
    >
      {isKnown ? "Known" : "Est."}
    </span>
  );
}
