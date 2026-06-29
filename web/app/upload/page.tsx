import Link from "next/link";

import { Disclaimer } from "@/components/Disclaimer";
import { ImportWizard } from "@/components/ImportWizard";

export default function UploadPage() {
  return (
    <div className="space-y-12 fade-up">
      <header className="space-y-3">
        <p className="label">Bring your portfolio in</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Pick your broker to start
        </h1>
        <p className="max-w-prose text-base leading-relaxed text-ink-muted">
          We&apos;ll show you exactly where to find the export. The file is parsed in place — we keep
          tickers, quantities, dates, and cost basis, nothing else. No broker login required.
        </p>
        <p className="text-sm text-ink-muted">
          Want to look around first?{" "}
          <Link href="/dashboard" className="font-medium text-accent hover:underline">
            Explore a sample portfolio →
          </Link>
        </p>
      </header>

      <ImportWizard />

      <section className="grid gap-4 sm:grid-cols-2">
        <article className="card p-5">
          <p className="label">Expected columns</p>
          <p className="mt-2 font-mono text-sm text-ink">
            date · type · ticker · isin · asset_class · quantity · unit_price_eur · fees_eur
          </p>
        </article>
        <article className="card p-5">
          <p className="label">No CSV yet?</p>
          <p className="mt-2 text-sm text-ink-muted">
            Use the sample at <code className="font-mono text-ink">api/app/seeds/sample-tr.csv</code>
            — also loaded by the seed script so the dashboard works out of the box.
          </p>
        </article>
      </section>

      <Disclaimer />
    </div>
  );
}
