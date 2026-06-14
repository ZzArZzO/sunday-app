import type { CryptoHoldingPeriodView, TaxSummaryResponse } from "@/lib/types";
import { formatDual, formatEur, formatPct } from "@/lib/format";

interface TaxCardProps {
  tax: TaxSummaryResponse;
}

export function TaxCard({ tax }: TaxCardProps) {
  const unrealised = Number(tax.unrealised_gains.eur);
  const isGain = unrealised > 0;
  const direction = isGain ? "gain" : unrealised === 0 ? "flat" : "loss";

  return (
    <article className="card p-5 sm:p-6">
      <header className="flex items-baseline justify-between gap-3">
        <div>
          <p className="label">Tax summary</p>
          <p className="mt-1 text-sm text-ink">
            {tax.country_name} ·{" "}
            <span className="font-mono">{formatPct(tax.base_rate_pct)} headline</span>
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${
            direction === "gain"
              ? "border-positive/30 bg-positive-subtle/40 text-positive"
              : direction === "loss"
                ? "border-negative/30 bg-negative-subtle/40 text-negative"
                : "border-rule bg-surface-2 text-ink-muted"
          }`}
        >
          {direction === "gain" ? "Unrealised gain" : direction === "loss" ? "Unrealised loss" : "Flat"}
        </span>
      </header>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Stat
          label="If you sold today"
          value={formatDual(tax.estimated_tax_if_realised).split(" / ")[0]}
          sub={`Net after tax: ${formatEur(tax.after_tax_value_if_realised.eur)}`}
        />
        <Stat
          label="Dividend tax / yr"
          value={formatDual(tax.estimated_dividend_tax).split(" / ")[0]}
          sub={`On ${formatEur(tax.annual_dividend_estimate.eur)} estimated income`}
        />
        <Stat
          label="Allowance"
          value={formatEur(tax.annual_allowance_eur)}
          sub="Annual tax-free amount"
        />
      </div>

      {tax.brackets.length > 0 ? (
        <div className="mt-5 space-y-2">
          <p className="label">Bracket structure</p>
          <ul className="divide-y divide-rule">
            {tax.brackets.map((bracket) => (
              <li key={bracket.label} className="flex items-baseline justify-between py-2 text-sm">
                <span className="text-ink">{bracket.label}</span>
                <span className="flex items-baseline gap-3 text-ink-muted">
                  <span className="text-xs">{bracket.applies_to}</span>
                  <span className="font-mono tabular-nums text-ink">
                    {formatPct(bracket.rate_pct)}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {tax.crypto_holding_periods.length > 0 ? (
        <div className="mt-5 space-y-2">
          <p className="label">Crypto holding period</p>
          <ul className="space-y-2">
            {tax.crypto_holding_periods.map((h, idx) => (
              <CryptoClock
                key={`${h.ticker}-${idx}`}
                holding={h}
                afterDays={tax.crypto_tax_free_after_days}
              />
            ))}
          </ul>
        </div>
      ) : null}

      {tax.notes.length > 0 ? (
        <ul className="mt-4 space-y-1 text-xs text-ink-subtle">
          {tax.notes.map((note, idx) => (
            <li key={idx}>· {note}</li>
          ))}
        </ul>
      ) : null}

      <p className="mt-4 text-xs italic text-ink-subtle">{tax.disclaimer}</p>
    </article>
  );
}

function CryptoClock({
  holding,
  afterDays,
}: {
  holding: CryptoHoldingPeriodView;
  afterDays: number | null;
}) {
  const denom = afterDays ?? 365;
  const pct = Math.min(100, Math.round((holding.days_held / denom) * 100));
  return (
    <li className="rounded-md border border-rule bg-surface-2/40 p-3">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium text-ink">{holding.ticker}</span>
        {holding.tax_free ? (
          <span className="inline-flex items-center rounded-md border border-positive/30 bg-positive-subtle/40 px-2 py-0.5 text-xs font-medium text-positive">
            Past the {denom}-day mark
          </span>
        ) : (
          <span className="font-mono text-xs text-ink-muted">
            {holding.days_to_tax_free} days to go
          </span>
        )}
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface-2">
        <div className="h-full rounded-full bg-positive" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-1.5 text-xs text-ink-subtle">
        Acquired {holding.acquired_on} · {holding.days_held} days held
      </p>
    </li>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-md border border-rule bg-surface-2/40 p-3">
      <p className="label">{label}</p>
      <p className="mt-1 font-mono text-lg tabular-nums text-ink">{value}</p>
      <p className="mt-1 text-xs text-ink-subtle">{sub}</p>
    </div>
  );
}
