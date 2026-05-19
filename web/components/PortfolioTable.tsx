import type { PositionView } from "@/lib/types";
import { formatDual, formatPct, formatQuantity } from "@/lib/format";

export function PortfolioTable({ positions }: { positions: PositionView[] }) {
  if (positions.length === 0) {
    return (
      <p className="text-sm text-ink-muted">
        No positions yet. Upload a CSV at <code>/upload</code>.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-ink/10 text-left text-ink-muted">
            <th className="py-2 pr-4 font-medium">Ticker</th>
            <th className="py-2 pr-4 font-medium">Class</th>
            <th className="py-2 pr-4 font-medium text-right">Quantity</th>
            <th className="py-2 pr-4 font-medium text-right">Avg cost (EUR)</th>
            <th className="py-2 pr-4 font-medium text-right">Market value (€ / $)</th>
            <th className="py-2 pr-4 font-medium text-right">P&amp;L (€ / $)</th>
            <th className="py-2 pr-4 font-medium text-right">Weight</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => {
            const pnlSign = Number(p.unrealised_pnl.eur);
            const pnlClass =
              pnlSign > 0 ? "text-positive" : pnlSign < 0 ? "text-negative" : "text-ink";
            return (
              <tr key={p.id} className="border-b border-ink/5">
                <td className="py-2 pr-4 font-medium">{p.ticker}</td>
                <td className="py-2 pr-4 text-ink-muted">{p.asset_class}</td>
                <td className="py-2 pr-4 text-right font-mono">
                  {formatQuantity(p.quantity, p.asset_class)}
                </td>
                <td className="py-2 pr-4 text-right font-mono">
                  {Number(p.avg_cost_eur).toFixed(4)}
                </td>
                <td className="py-2 pr-4 text-right font-mono">{formatDual(p.market_value)}</td>
                <td className={`py-2 pr-4 text-right font-mono ${pnlClass}`}>
                  {formatDual(p.unrealised_pnl)}
                </td>
                <td className="py-2 pr-4 text-right font-mono">{formatPct(p.weight_pct)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
