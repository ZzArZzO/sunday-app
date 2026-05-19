import type { PositionView } from "@/lib/types";
import { formatDual, formatPct, formatQuantity } from "@/lib/format";

const ASSET_CLASS_LABEL: Record<string, string> = {
  stock: "Stock",
  etf: "ETF",
  crypto: "Crypto",
  cash: "Cash",
};

export function PortfolioTable({ positions }: { positions: PositionView[] }) {
  if (positions.length === 0) {
    return (
      <div className="card p-10 text-center">
        <p className="label">No positions yet</p>
        <p className="mt-2 text-ink-muted">
          Upload a CSV at <code className="font-mono text-ink">/upload</code> to populate this view.
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule bg-surface-2/60 text-left">
              <Th>Ticker</Th>
              <Th>Class</Th>
              <Th align="right">Quantity</Th>
              <Th align="right">Avg cost</Th>
              <Th align="right">Market value</Th>
              <Th align="right">P&amp;L</Th>
              <Th align="right">Weight</Th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p, idx) => {
              const pnl = Number(p.unrealised_pnl.eur);
              const pnlClass =
                pnl > 0 ? "text-positive" : pnl < 0 ? "text-negative" : "text-ink-muted";
              const isLast = idx === positions.length - 1;
              return (
                <tr
                  key={p.id}
                  className={`transition-colors hover:bg-surface-2/40 ${
                    isLast ? "" : "border-b border-rule"
                  }`}
                >
                  <Td>
                    <span className="font-semibold text-ink">{p.ticker}</span>
                    {p.isin ? (
                      <span className="ml-2 font-mono text-xs text-ink-subtle">{p.isin}</span>
                    ) : null}
                  </Td>
                  <Td>
                    <span className="inline-flex items-center rounded-md border border-rule bg-surface-2 px-2 py-0.5 text-xs font-medium text-ink-muted">
                      {ASSET_CLASS_LABEL[p.asset_class] ?? p.asset_class}
                    </span>
                  </Td>
                  <Td align="right" mono>
                    {formatQuantity(p.quantity, p.asset_class)}
                  </Td>
                  <Td align="right" mono>
                    {Number(p.avg_cost_eur).toFixed(2)}
                  </Td>
                  <Td align="right" mono>
                    {formatDual(p.market_value)}
                  </Td>
                  <Td align="right" mono className={pnlClass}>
                    {pnl > 0 ? "+" : ""}
                    {formatDual(p.unrealised_pnl)}
                  </Td>
                  <Td align="right" mono>
                    {formatPct(p.weight_pct)}
                  </Td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({
  children,
  align = "left",
}: {
  children: React.ReactNode;
  align?: "left" | "right";
}) {
  return (
    <th
      className={`label px-4 py-3 ${align === "right" ? "text-right" : "text-left"}`}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  align = "left",
  mono = false,
  className = "",
}: {
  children: React.ReactNode;
  align?: "left" | "right";
  mono?: boolean;
  className?: string;
}) {
  return (
    <td
      className={`px-4 py-3 ${align === "right" ? "text-right" : "text-left"} ${
        mono ? "font-mono text-ink" : "text-ink"
      } ${className}`}
    >
      {children}
    </td>
  );
}
