import { ConcentrationCard } from "@/components/ConcentrationCard";
import { Disclaimer } from "@/components/Disclaimer";
import { PortfolioTable } from "@/components/PortfolioTable";
import { fetchPortfolio } from "@/lib/api";
import { formatDual, formatPct } from "@/lib/format";

export const dynamic = "force-dynamic";

const ASSET_CLASS_LABEL: Record<string, string> = {
  stock: "Stocks",
  etf: "ETFs",
  crypto: "Crypto",
  cash: "Cash",
};

export default async function DashboardPage() {
  let data;
  try {
    data = await fetchPortfolio();
  } catch (err) {
    return (
      <div className="card border-negative/30 bg-negative-subtle/40 p-5">
        <p className="font-medium text-negative">Couldn&apos;t load portfolio</p>
        <p className="mt-2 text-sm text-ink">
          {err instanceof Error ? err.message : String(err)}
        </p>
        <p className="mt-2 text-sm text-ink-muted">
          Make sure the API is running on <code className="font-mono">localhost:8000</code> and
          that you ran <code className="font-mono">python -m app.seeds.load_sample</code>.
        </p>
      </div>
    );
  }

  const pnl = Number(data.total_pnl.eur);
  const pnlClass =
    pnl > 0 ? "text-positive" : pnl < 0 ? "text-negative" : "text-ink-muted";
  const pnlSign = pnl > 0 ? "+" : "";

  return (
    <div className="space-y-12 fade-up">
      <header className="space-y-4">
        <p className="label">As of {new Date(data.as_of).toLocaleDateString()}</p>
        <h1 className="font-sans text-5xl font-semibold leading-none tracking-tighter text-ink sm:text-6xl">
          {formatDual(data.total_value)}
        </h1>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink-muted">
          <Stat label="Cost basis" value={formatDual(data.total_cost)} />
          <Stat
            label="Unrealised"
            value={`${pnlSign}${formatDual(data.total_pnl)}`}
            valueClass={pnlClass}
          />
          <Stat label="EUR/USD" value={Number(data.fx_eur_usd).toFixed(4)} />
        </div>
      </header>

      <section className="space-y-4">
        <p className="label">By asset class</p>
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Object.entries(data.asset_class_split).map(([cls, pct]) => (
            <li key={cls} className="card p-4">
              <p className="label">{ASSET_CLASS_LABEL[cls] ?? cls}</p>
              <p className="mt-1 font-mono text-2xl tabular-nums text-ink">{formatPct(pct)}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-4">
        <p className="label">Concentration</p>
        <ConcentrationCard items={data.concentration} />
      </section>

      <section className="space-y-4">
        <p className="label">Positions</p>
        <PortfolioTable positions={data.positions} />
      </section>

      <Disclaimer
        extra={`Prices on the demo portfolio are placeholder values. As of ${new Date(
          data.as_of,
        ).toLocaleString()}.`}
      />
    </div>
  );
}

function Stat({
  label,
  value,
  valueClass = "",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <span className="inline-flex items-baseline gap-2">
      <span className="text-ink-subtle">{label}</span>
      <span className={`font-mono tabular-nums ${valueClass || "text-ink"}`}>{value}</span>
    </span>
  );
}
