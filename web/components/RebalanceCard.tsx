import type { RebalanceLeg, RebalanceResponse } from "@/lib/types";
import { formatEur, formatPct } from "@/lib/format";

interface RebalanceCardProps {
  rebalance: RebalanceResponse;
}

const ASSET_CLASS_LABEL: Record<string, string> = {
  etf: "ETFs",
  stock: "Stocks",
  crypto: "Crypto",
  cash: "Cash",
};

export function RebalanceCard({ rebalance }: RebalanceCardProps) {
  return (
    <article className="card p-5 sm:p-6">
      <header className="flex items-baseline justify-between gap-3">
        <div>
          <p className="label">Rebalance check</p>
          <p className="mt-1 text-sm text-ink">
            Drift score{" "}
            <span className="font-mono tabular-nums">{Number(rebalance.drift_score).toFixed(1)}</span>
          </p>
        </div>
        <StatusBadge needsRebalance={rebalance.needs_rebalance} />
      </header>

      <ul className="mt-4 divide-y divide-rule">
        {rebalance.legs.map((leg) => (
          <RebalanceLegRow key={leg.asset_class} leg={leg} />
        ))}
      </ul>

      {rebalance.notes.length > 0 ? (
        <ul className="mt-4 space-y-1 text-xs text-ink-subtle">
          {rebalance.notes.map((note, idx) => (
            <li key={idx}>· {note}</li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function StatusBadge({ needsRebalance }: { needsRebalance: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${
        needsRebalance
          ? "border-warn/30 bg-warn-subtle/40 text-warn"
          : "border-positive/30 bg-positive-subtle/40 text-positive"
      }`}
    >
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full ${
          needsRebalance ? "bg-warn" : "bg-positive"
        }`}
      />
      {needsRebalance ? "Drift > 5%" : "In balance"}
    </span>
  );
}

function RebalanceLegRow({ leg }: { leg: RebalanceLeg }) {
  const drift = Number(leg.drift_pct);
  const driftSign = drift > 0 ? "+" : "";
  const driftClass =
    leg.action === "hold"
      ? "text-ink-subtle"
      : drift > 0
        ? "text-warn"
        : "text-accent";

  const deltaEur = Number(leg.delta.eur);
  const actionLabel =
    leg.action === "hold"
      ? "Hold"
      : leg.action === "buy"
        ? `Buy ${formatEur(Math.abs(deltaEur))}`
        : `Sell ${formatEur(Math.abs(deltaEur))}`;

  return (
    <li className="grid grid-cols-[auto_1fr_auto] items-center gap-3 py-3 text-sm">
      <div className="min-w-[88px]">
        <p className="font-medium text-ink">
          {ASSET_CLASS_LABEL[leg.asset_class] ?? leg.asset_class}
        </p>
        <p className="font-mono text-xs text-ink-subtle">
          {formatPct(leg.current_pct)} → {formatPct(leg.target_pct)}
        </p>
      </div>

      <DriftBar currentPct={Number(leg.current_pct)} targetPct={Number(leg.target_pct)} />

      <div className="text-right">
        <p className={`font-mono text-xs ${driftClass}`}>
          {driftSign}
          {drift.toFixed(2)}%
        </p>
        <p className="mt-0.5 text-xs text-ink-muted">{actionLabel}</p>
      </div>
    </li>
  );
}

function DriftBar({ currentPct, targetPct }: { currentPct: number; targetPct: number }) {
  const max = Math.max(currentPct, targetPct, 1);
  return (
    <div className="relative h-2 w-full overflow-hidden rounded-full bg-surface-2">
      <div
        className="absolute left-0 top-0 h-full rounded-full bg-ink/30"
        style={{ width: `${(targetPct / max) * 100}%` }}
        aria-hidden
      />
      <div
        className="absolute left-0 top-0 h-full rounded-full bg-accent"
        style={{ width: `${(currentPct / max) * 100}%` }}
        aria-hidden
      />
    </div>
  );
}
