import { Disclaimer } from "@/components/Disclaimer";
import { DividendCard } from "@/components/DividendCard";
import { FireCard } from "@/components/FireCard";
import { RebalanceCard } from "@/components/RebalanceCard";
import { TaxCard } from "@/components/TaxCard";
import { DIVIDEND_SNAPSHOT, FIRE_SNAPSHOT, REBALANCE_SNAPSHOT, TAX_SNAPSHOT } from "@/lib/planSnapshot";

/**
 * The "Plan" hub — groups the lower-frequency analytical views (financial
 * independence, dividend income, tax outlook, rebalancing) behind one mobile
 * tab, per the mobile UX research. Information only, never advice.
 *
 * FIRE progress leads at full width since it's the one figure on this page
 * with an emotional arc — everything else here supports it as context.
 */
export default function PlanPage() {
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

      <FireCard fire={FIRE_SNAPSHOT} />

      <section className="grid gap-4 lg:grid-cols-2">
        <DividendCard dividend={DIVIDEND_SNAPSHOT} />
        <RebalanceCard rebalance={REBALANCE_SNAPSHOT} />
      </section>

      <TaxCard tax={TAX_SNAPSHOT} />

      <Disclaimer />
    </div>
  );
}
