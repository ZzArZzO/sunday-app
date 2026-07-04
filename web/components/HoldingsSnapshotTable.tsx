import { GainLossTag } from "@/components/GainLossTag";
import { formatEurWhole, formatSignedPct, formatWeightPct } from "@/lib/moneyFormat";
import type { HoldingSnapshot, PortfolioSnapshot } from "@/lib/portfolioSnapshot";

export interface HoldingsSnapshotTableProps {
  holdings: HoldingSnapshot[];
  total: Pick<PortfolioSnapshot, "netWorthEur" | "totalPnlPct">;
}

/**
 * Instrument / Value / P&L / Weight. Weight gets its own neutral proportion
 * bar — it's a share of the portfolio, not a monetary gain or loss, so it
 * deliberately never touches the blue/orange pair.
 */
export function HoldingsSnapshotTable({ holdings, total }: HoldingsSnapshotTableProps) {
  return (
    <>
      {/* Mobile: stacked cards. */}
      <ul className="space-y-3 md:hidden">
        {holdings.map((h) => (
          <li key={h.ticker} className="card p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold text-ink">{h.ticker}</p>
                <p className="truncate text-xs text-ink-subtle">{h.name}</p>
              </div>
              <div className="text-right">
                <p className="font-mono tabular-nums text-ink">{formatEurWhole(h.valueEur)}</p>
                <GainLossTag
                  value={h.pnlPct}
                  label={formatSignedPct(h.pnlPct)}
                  className="mt-0.5 justify-end"
                />
              </div>
            </div>
            <WeightBar weightPct={h.weightPct} className="mt-3" />
          </li>
        ))}
        <li className="card p-4">
          <div className="flex items-start justify-between gap-3">
            <p className="font-semibold text-ink">Total</p>
            <div className="text-right">
              <p className="font-mono tabular-nums text-ink">{formatEurWhole(total.netWorthEur)}</p>
              <GainLossTag
                value={total.totalPnlPct}
                label={formatSignedPct(total.totalPnlPct)}
                className="mt-0.5 justify-end"
              />
            </div>
          </div>
          <WeightBar weightPct={100} className="mt-3" />
        </li>
      </ul>

      {/* Desktop: full table, numeric columns right-aligned with tabular figures. */}
      <div className="card hidden overflow-hidden md:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule bg-surface-2/60 text-left">
              <Th>Instrument</Th>
              <Th align="right">Value</Th>
              <Th align="right">P&amp;L</Th>
              <Th align="right">Weight</Th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => (
              <tr key={h.ticker} className="border-b border-rule transition-colors hover:bg-surface-2/40">
                <Td>
                  <span className="font-semibold text-ink">{h.ticker}</span>
                  <span className="ml-2 text-ink-subtle">{h.name}</span>
                </Td>
                <Td align="right" mono>
                  {formatEurWhole(h.valueEur)}
                </Td>
                <Td align="right">
                  <GainLossTag value={h.pnlPct} label={formatSignedPct(h.pnlPct)} className="justify-end" />
                </Td>
                <Td align="right">
                  <div className="flex items-center justify-end gap-3">
                    <WeightBar weightPct={h.weightPct} className="w-20" />
                    <span className="w-10 font-mono tabular-nums text-ink">
                      {formatWeightPct(h.weightPct)}
                    </span>
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-rule bg-surface-2/40 font-semibold">
              <Td>Total</Td>
              <Td align="right" mono>
                {formatEurWhole(total.netWorthEur)}
              </Td>
              <Td align="right">
                <GainLossTag
                  value={total.totalPnlPct}
                  label={formatSignedPct(total.totalPnlPct)}
                  className="justify-end"
                />
              </Td>
              <Td align="right">
                <div className="flex items-center justify-end gap-3">
                  <WeightBar weightPct={100} className="w-20" />
                  <span className="w-10 font-mono tabular-nums text-ink">100%</span>
                </div>
              </Td>
            </tr>
          </tfoot>
        </table>
      </div>
    </>
  );
}

function WeightBar({ weightPct, className = "" }: { weightPct: number; className?: string }) {
  return (
    <div
      role="img"
      aria-label={`${formatWeightPct(weightPct)} of portfolio`}
      className={`h-1.5 overflow-hidden rounded-full bg-surface-2 ${className}`}
    >
      <div className="h-full rounded-full bg-ink-subtle" style={{ width: `${weightPct}%` }} />
    </div>
  );
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return <th className={`label px-4 py-3 ${align === "right" ? "text-right" : "text-left"}`}>{children}</th>;
}

function Td({
  children,
  align = "left",
  mono = false,
}: {
  children: React.ReactNode;
  align?: "left" | "right";
  mono?: boolean;
}) {
  return (
    <td className={`px-4 py-3 ${align === "right" ? "text-right" : "text-left"} ${mono ? "font-mono text-ink" : "text-ink"}`}>
      {children}
    </td>
  );
}
