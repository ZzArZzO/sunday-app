"use client";

import { useState } from "react";

import { BottomSheet } from "@/components/BottomSheet";
import { TrendArrow } from "@/components/TrendArrow";
import { formatDual, formatEur, formatPct, formatQuantity } from "@/lib/format";
import { DEFAULT_LOCALE, type SupportedLocale } from "@/lib/locale";
import type { PositionView } from "@/lib/types";

const ASSET_CLASS_LABEL: Record<string, string> = {
  stock: "Stock",
  etf: "ETF",
  crypto: "Crypto",
  cash: "Cash",
};

function pnlClassFor(pnl: number): string {
  return pnl > 0 ? "text-positive" : pnl < 0 ? "text-negative" : "text-ink-muted";
}

function pnlPctOf(position: PositionView): number {
  const cost = Number(position.cost_basis.eur);
  return cost > 0 ? (Number(position.unrealised_pnl.eur) / cost) * 100 : 0;
}

/** Mobile holdings: one tappable card per position; tap opens a detail sheet. */
export function HoldingsMobileList({
  positions,
  locale = DEFAULT_LOCALE,
}: {
  positions: PositionView[];
  locale?: SupportedLocale;
}) {
  const [selected, setSelected] = useState<PositionView | null>(null);

  return (
    <>
      <ul className="space-y-3 md:hidden">
        {positions.map((p) => {
          const pnl = Number(p.unrealised_pnl.eur);
          return (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => setSelected(p)}
                className="card w-full p-4 text-left transition-colors hover:bg-surface-2/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-ink">{p.ticker}</span>
                      <span className="inline-flex items-center rounded-md border border-rule bg-surface-2 px-1.5 py-0.5 text-[11px] font-medium text-ink-muted">
                        {ASSET_CLASS_LABEL[p.asset_class] ?? p.asset_class}
                      </span>
                    </div>
                    {p.isin ? (
                      <span className="mt-0.5 block font-mono text-xs text-ink-subtle">{p.isin}</span>
                    ) : null}
                  </div>
                  <div className="text-right">
                    <p className="font-mono tabular-nums text-ink">{formatEur(p.market_value.eur, locale)}</p>
                    <p
                      className={`mt-0.5 inline-flex items-center justify-end gap-1 font-mono text-xs tabular-nums ${pnlClassFor(pnl)}`}
                    >
                      <TrendArrow value={pnl} size={11} />
                      {pnl > 0 ? "+" : ""}
                      {formatPct(String(pnlPctOf(p)), locale)}
                    </p>
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-ink-subtle">
                  <span className="font-mono">
                    {formatQuantity(p.quantity, p.asset_class, locale)} @ {formatEur(p.avg_cost_eur, locale)}
                  </span>
                  <span>
                    Weight <span className="font-mono text-ink-muted">{formatPct(p.weight_pct, locale)}</span>
                  </span>
                </div>
              </button>
            </li>
          );
        })}
      </ul>

      <BottomSheet
        open={selected !== null}
        onClose={() => setSelected(null)}
        title={selected?.ticker}
      >
        {selected ? <HoldingDetail position={selected} locale={locale} /> : null}
      </BottomSheet>
    </>
  );
}

function HoldingDetail({ position, locale }: { position: PositionView; locale: SupportedLocale }) {
  const pnl = Number(position.unrealised_pnl.eur);
  const rows: { label: string; value: string; className?: string }[] = [
    { label: "Asset class", value: ASSET_CLASS_LABEL[position.asset_class] ?? position.asset_class },
    { label: "Quantity", value: formatQuantity(position.quantity, position.asset_class, locale) },
    { label: "Average cost", value: formatEur(position.avg_cost_eur, locale) },
    {
      label: "Last price",
      value: position.last_price_eur ? formatEur(position.last_price_eur, locale) : "—",
    },
    { label: "Market value", value: formatDual(position.market_value, locale) },
    { label: "Cost basis", value: formatDual(position.cost_basis, locale) },
    {
      label: "Unrealised P&L",
      value: `${pnl > 0 ? "+" : ""}${formatDual(position.unrealised_pnl, locale)} (${formatPct(String(pnlPctOf(position)), locale)})`,
      className: pnlClassFor(pnl),
    },
    { label: "Weight", value: formatPct(position.weight_pct, locale) },
  ];

  return (
    <dl className="divide-y divide-rule">
      {position.isin ? (
        <div className="flex items-center justify-between py-2.5 text-sm">
          <dt className="text-ink-muted">ISIN</dt>
          <dd className="font-mono text-ink-subtle">{position.isin}</dd>
        </div>
      ) : null}
      {rows.map((row) => (
        <div key={row.label} className="flex items-center justify-between gap-4 py-2.5 text-sm">
          <dt className="text-ink-muted">{row.label}</dt>
          <dd className={`font-mono tabular-nums text-ink ${row.className ?? ""}`}>{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}
