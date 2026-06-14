import type { ConcentrationItem } from "@/lib/types";
import { formatPct } from "@/lib/format";
import { DEFAULT_LOCALE, type SupportedLocale } from "@/lib/locale";

const SEVERITY_STYLES: Record<
  ConcentrationItem["severity"],
  { dot: string; label: string; tag: string }
> = {
  info: {
    dot: "bg-ink-subtle",
    label: "text-ink-muted",
    tag: "border-rule bg-surface-2 text-ink-muted",
  },
  warning: {
    dot: "bg-warn",
    label: "text-warn",
    tag: "border-warn/30 bg-warn-subtle/60 text-warn",
  },
  alert: {
    dot: "bg-negative",
    label: "text-negative",
    tag: "border-negative/30 bg-negative-subtle/60 text-negative",
  },
};

export function ConcentrationCard({
  items,
  locale = DEFAULT_LOCALE,
}: {
  items: ConcentrationItem[];
  locale?: SupportedLocale;
}) {
  if (items.length === 0) {
    return (
      <div className="card p-5">
        <p className="flex items-center gap-2 text-sm text-ink-muted">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-positive" />
          No positions cross your configured thresholds this week.
        </p>
      </div>
    );
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {items.map((item) => {
        const styles = SEVERITY_STYLES[item.severity];
        return (
          <li key={item.ticker} className="card p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`inline-block h-1.5 w-1.5 rounded-full ${styles.dot}`} />
                <span className={`label ${styles.label}`}>{item.severity}</span>
              </div>
              <span
                className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${styles.tag}`}
              >
                Above {formatPct(item.threshold_pct, locale)}
              </span>
            </div>
            <div className="mt-3 flex items-baseline justify-between gap-4">
              <span className="font-sans text-lg font-semibold tracking-tight text-ink">
                {item.ticker}
              </span>
              <span className="font-mono text-2xl tabular-nums text-ink">
                {formatPct(item.weight_pct, locale)}
              </span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
