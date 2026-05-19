import { ConcentrationCard } from "@/components/ConcentrationCard";
import { Disclaimer } from "@/components/Disclaimer";
import { PortfolioTable } from "@/components/PortfolioTable";
import { fetchPortfolio } from "@/lib/api";
import { formatDual, formatPct } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let data;
  try {
    data = await fetchPortfolio();
  } catch (err) {
    return (
      <div className="rounded-md border border-negative/30 bg-negative/5 p-6 text-sm text-negative">
        <p className="font-medium">Couldn&apos;t load portfolio.</p>
        <p className="mt-2">{err instanceof Error ? err.message : String(err)}</p>
        <p className="mt-3">
          Make sure the API is running on <code>localhost:8000</code> and that you ran{" "}
          <code>python -m app.seeds.load_sample</code> (or uploaded a CSV).
        </p>
      </div>
    );
  }

  const totalPnlSign = Number(data.total_pnl.eur);
  const pnlClass =
    totalPnlSign > 0 ? "text-positive" : totalPnlSign < 0 ? "text-negative" : "text-ink";

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-wide text-ink-subtle">Dashboard</p>
        <h1 className="text-3xl font-semibold">{formatDual(data.total_value)}</h1>
        <p className="text-sm text-ink-muted">
          Cost: {formatDual(data.total_cost)} · P&amp;L:{" "}
          <span className={pnlClass}>{formatDual(data.total_pnl)}</span> · FX EUR/USD{" "}
          {Number(data.fx_eur_usd).toFixed(4)}
        </p>
      </header>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Asset class split</h2>
        <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(data.asset_class_split).map(([cls, pct]) => (
            <li key={cls} className="rounded-md border border-ink/10 bg-paper-card p-3">
              <p className="text-xs uppercase tracking-wide text-ink-subtle">{cls}</p>
              <p className="text-lg font-medium">{formatPct(pct)}</p>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Concentration</h2>
        <ConcentrationCard items={data.concentration} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Positions</h2>
        <div className="rounded-lg border border-ink/10 bg-paper-card p-4">
          <PortfolioTable positions={data.positions} />
        </div>
      </section>

      <Disclaimer
        extra={`As of ${new Date(data.as_of).toLocaleString()}. Sample prices for MVP preview — not live.`}
      />
    </div>
  );
}
