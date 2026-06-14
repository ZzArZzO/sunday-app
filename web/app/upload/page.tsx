import Link from "next/link";

import { CsvUploader } from "@/components/CsvUploader";
import { Disclaimer } from "@/components/Disclaimer";

export default function UploadPage() {
  return (
    <div className="space-y-12 fade-up">
      <header className="space-y-3">
        <p className="label">Step 1 of 1</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Bring your portfolio in
        </h1>
        <p className="max-w-prose text-base leading-relaxed text-ink-muted">
          Export your position history from your broker as CSV and drop it in. The file is parsed
          in place. We keep tickers, quantities, dates, and cost basis — nothing else.
        </p>
        <p className="text-sm text-ink-muted">
          Want to look around first?{" "}
          <Link href="/dashboard" className="font-medium text-accent hover:underline">
            Explore a sample portfolio →
          </Link>
        </p>
      </header>

      <CsvUploader />

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
