import { formatPct } from "@/lib/format";
import { DEFAULT_LOCALE, type SupportedLocale } from "@/lib/locale";

// A calm, zero-dependency 100%-stacked allocation bar with a legend. Replaces
// the flat percentage-card grid. Top-level split only (asset class); the
// per-holding treemap is a later, heatmap-style view.

const ASSET_CLASS_LABEL: Record<string, string> = {
  stock: "Stocks",
  etf: "ETFs",
  crypto: "Crypto",
  cash: "Cash",
  bond: "Bonds",
};

// Categorical, colour-blind-distinct hues (not the gain/loss pair). Ordered to
// match the usual largest-to-smallest classes.
const SEGMENT_COLORS = [
  "rgb(37 99 235)", // blue
  "rgb(217 119 6)", // amber
  "rgb(124 58 237)", // violet
  "rgb(13 148 136)", // teal
  "rgb(219 39 119)", // pink
  "rgb(101 113 130)", // slate
];

type Segment = { cls: string; label: string; pct: number; color: string };

function buildSegments(split: Record<string, string>): Segment[] {
  return Object.entries(split)
    .map(([cls, pct]) => ({ cls, pct: Number(pct) }))
    .sort((a, b) => b.pct - a.pct)
    .map((s, i) => ({
      cls: s.cls,
      label: ASSET_CLASS_LABEL[s.cls] ?? s.cls,
      pct: s.pct,
      color: SEGMENT_COLORS[i % SEGMENT_COLORS.length],
    }));
}

export function AllocationBar({
  split,
  locale = DEFAULT_LOCALE,
}: {
  split: Record<string, string>;
  locale?: SupportedLocale;
}) {
  const segments = buildSegments(split);
  if (segments.length === 0) {
    return <p className="text-sm text-ink-muted">No allocation to show yet.</p>;
  }

  const ariaLabel =
    "Allocation by asset class: " +
    segments.map((s) => `${s.label} ${s.pct.toFixed(1)}%`).join(", ");

  return (
    <div className="space-y-4">
      <div
        role="img"
        aria-label={ariaLabel}
        className="flex h-3 w-full overflow-hidden rounded-full bg-surface-2"
      >
        {segments.map((s) => (
          <div
            key={s.cls}
            className="h-full first:rounded-l-full last:rounded-r-full"
            style={{ width: `${s.pct}%`, backgroundColor: s.color }}
            title={`${s.label} · ${s.pct.toFixed(1)}%`}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-6 gap-y-2">
        {segments.map((s) => (
          <li key={s.cls} className="flex items-center gap-2 text-sm">
            <span
              aria-hidden
              className="inline-block h-2.5 w-2.5 flex-none rounded-sm"
              style={{ backgroundColor: s.color }}
            />
            <span className="text-ink-muted">{s.label}</span>
            <span className="font-mono tabular-nums text-ink">{formatPct(String(s.pct), locale)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
