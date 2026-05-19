import type { ConcentrationItem } from "@/lib/types";
import { formatPct } from "@/lib/format";

const SEVERITY_STYLES: Record<ConcentrationItem["severity"], string> = {
  info: "border-ink/10 bg-ink/5 text-ink-muted",
  warning: "border-amber-300 bg-amber-50 text-amber-900",
  alert: "border-negative/40 bg-negative/5 text-negative",
};

export function ConcentrationCard({ items }: { items: ConcentrationItem[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-md border border-positive/20 bg-positive/5 p-4 text-sm text-positive">
        No positions cross your concentration thresholds.
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.ticker}
          className={`rounded-md border p-3 text-sm ${SEVERITY_STYLES[item.severity]}`}
        >
          <div className="flex items-baseline justify-between">
            <span className="font-medium">{item.ticker}</span>
            <span className="font-mono">{formatPct(item.weight_pct)}</span>
          </div>
          <p className="mt-1 text-xs opacity-80">
            Your {item.severity} threshold: {formatPct(item.threshold_pct)}
          </p>
        </li>
      ))}
    </ul>
  );
}
