"use client";

import { Disclaimer } from "@/components/Disclaimer";
import { DividendCard } from "@/components/DividendCard";
import { FireCard } from "@/components/FireCard";
import { RebalanceCard } from "@/components/RebalanceCard";
import { TaxCard } from "@/components/TaxCard";
import { fetchDividend, fetchFire, fetchRebalance, fetchTax } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";

/**
 * The "Plan" hub — groups the lower-frequency analytical views (financial
 * independence, dividend income, tax outlook, rebalancing) behind one mobile
 * tab, per the mobile UX research. Information only, never advice.
 *
 * FIRE progress leads at full width since it's the one figure on this page
 * with an emotional arc — everything else here supports it as context.
 */
export default function PlanPage() {
  const { data, loading, error } = useAsync(() =>
    Promise.all([fetchFire(), fetchDividend(), fetchTax(), fetchRebalance()]),
  );

  if (loading) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="skeleton h-48 w-full" />
        <div className="skeleton h-48 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card border-negative/30 bg-negative-subtle/40 p-5">
        <p className="font-medium text-negative">Couldn&apos;t load your plan</p>
        <p className="mt-2 text-sm text-ink">{error}</p>
      </div>
    );
  }

  const [fire, dividend, tax, rebalance] = data;

  return (
    <div className="space-y-10 fade-up sm:space-y-12">
      <header className="space-y-2">
        <p className="label">Plan</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Plan &amp; projections
        </h1>
        <p className="max-w-prose text-sm leading-relaxed text-ink-muted">
          Financial independence, dividend income, tax outlook, and rebalancing — information only,
          not advice.
        </p>
      </header>

      <FireCard fire={fire} />

      <section className="grid gap-4 lg:grid-cols-2">
        <DividendCard dividend={dividend} />
        <RebalanceCard rebalance={rebalance} />
      </section>

      <TaxCard tax={tax} />

      <Disclaimer />
    </div>
  );
}
