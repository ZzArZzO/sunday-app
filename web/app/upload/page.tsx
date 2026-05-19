import { CsvUploader } from "@/components/CsvUploader";
import { Disclaimer } from "@/components/Disclaimer";

export default function UploadPage() {
  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">Upload your Trade Republic CSV</h1>
        <p className="text-ink-muted">
          The file is parsed in-place — we keep positions, quantities, and cost basis only. PII columns
          (names, IBANs, account IDs) are never read.
        </p>
      </header>

      <section className="rounded-lg border border-ink/10 bg-paper-card p-6">
        <CsvUploader />
      </section>

      <section className="rounded-lg border border-ink/10 bg-paper-card p-6 text-sm text-ink-muted">
        <h2 className="font-medium text-ink">Expected columns</h2>
        <p className="mt-2">
          <code className="font-mono">
            date, type, ticker, isin, asset_class, quantity, unit_price_eur, fees_eur
          </code>
        </p>
        <p className="mt-3">
          For the MVP slice you can also use{" "}
          <code className="font-mono">api/app/seeds/sample-tr.csv</code> from the repo.
        </p>
      </section>

      <Disclaimer />
    </div>
  );
}
