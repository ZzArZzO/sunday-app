import { AllocationBar } from "@/components/AllocationBar";
import { AllocationTreemap } from "@/components/AllocationTreemap";
import { BenchmarkChart } from "@/components/BenchmarkChart";
import { ConcentrationCard } from "@/components/ConcentrationCard";
import { DataQualityNote } from "@/components/DataQualityNote";
import { Disclaimer } from "@/components/Disclaimer";
import { DividendCard } from "@/components/DividendCard";
import { FireCard } from "@/components/FireCard";
import { PortfolioTable } from "@/components/PortfolioTable";
import { RebalanceCard } from "@/components/RebalanceCard";
import { RefreshPricesButton } from "@/components/RefreshPricesButton";
import { TaxCard } from "@/components/TaxCard";
import { TrendArrow } from "@/components/TrendArrow";
import {
  fetchDividend,
  fetchFire,
  fetchPortfolio,
  fetchRebalance,
  fetchTax,
} from "@/lib/api";
import { formatDual } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let portfolio;
  let fire;
  let dividend;
  let tax;
  let rebalance;
  try {
    [portfolio, fire, dividend, tax, rebalance] = await Promise.all([
      fetchPortfolio(),
      fetchFire(),
      fetchDividend(),
      fetchTax(),
      fetchRebalance(),
    ]);
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

  const pnl = Number(portfolio.total_pnl.eur);
  const pnlClass =
    pnl > 0 ? "text-positive" : pnl < 0 ? "text-negative" : "text-ink-muted";
  const pnlSign = pnl > 0 ? "+" : "";
  const pricedCount = portfolio.positions.filter((p) => p.last_price_eur !== null).length;

  return (
    <div className="space-y-10 fade-up sm:space-y-12">
      <header className="space-y-4">
        <p className="label">As of {new Date(portfolio.as_of).toLocaleDateString()}</p>
        <h1 className="font-sans text-4xl font-semibold leading-none tracking-tighter text-ink sm:text-5xl md:text-6xl">
          {formatDual(portfolio.total_value)}
        </h1>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink-muted">
          <Stat label="Cost basis" value={formatDual(portfolio.total_cost)} />
          <Stat
            label="Unrealised"
            value={`${pnlSign}${formatDual(portfolio.total_pnl)}`}
            valueClass={pnlClass}
            trend={pnl}
          />
        </div>
        <DataQualityNote
          asOf={portfolio.as_of}
          priced={pricedCount}
          total={portfolio.positions.length}
          fxEurUsd={portfolio.fx_eur_usd}
        />
        <RefreshPricesButton />
      </header>

      <section className="space-y-4">
        <p className="label">By asset class</p>
        <div className="card p-5">
          <AllocationBar split={portfolio.asset_class_split} />
        </div>
      </section>

      <BenchmarkChart />

      <section className="grid gap-4 lg:grid-cols-2">
        <FireCard fire={fire} />
        <DividendCard dividend={dividend} />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <RebalanceCard rebalance={rebalance} />
        <TaxCard tax={tax} />
      </section>

      <section className="space-y-4">
        <p className="label">Concentration</p>
        <ConcentrationCard items={portfolio.concentration} />
      </section>

      <section className="space-y-4">
        <div className="flex items-baseline justify-between gap-4">
          <p className="label">Holdings map</p>
          <p className="text-xs text-ink-subtle">
            Tile size = value · colour = gain/loss
          </p>
        </div>
        <div className="card p-5">
          <AllocationTreemap positions={portfolio.positions} />
        </div>
      </section>

      <section className="space-y-4">
        <p className="label">Positions</p>
        <PortfolioTable positions={portfolio.positions} />
      </section>

      <Disclaimer
        extra={`Use "Refresh prices" for live values; unpriced holdings fall back to cost basis. As of ${new Date(
          portfolio.as_of,
        ).toLocaleString()}.`}
      />
    </div>
  );
}

function Stat({
  label,
  value,
  valueClass = "",
  trend,
}: {
  label: string;
  value: string;
  valueClass?: string;
  trend?: number;
}) {
  return (
    <span className="inline-flex items-baseline gap-2">
      <span className="text-ink-subtle">{label}</span>
      <span className={`inline-flex items-center gap-1 font-mono tabular-nums ${valueClass || "text-ink"}`}>
        {trend !== undefined ? <TrendArrow value={trend} className={valueClass} /> : null}
        {value}
      </span>
    </span>
  );
}
