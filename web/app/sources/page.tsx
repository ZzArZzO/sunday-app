import { Disclaimer } from "@/components/Disclaimer";
import { SourcesManager } from "@/components/SourcesManager";

export default function SourcesPage() {
  return (
    <div className="space-y-12 fade-up">
      <header className="space-y-3">
        <p className="label">Your data</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Sources
        </h1>
        <p className="max-w-prose text-base leading-relaxed text-ink-muted">
          Everything feeding your portfolio in one place. Import a broker CSV, connect an Ethereum or
          Solana wallet, or link an exchange like Bitvavo for live, read-only sync. Disconnect anything any
          time.
        </p>
      </header>

      <SourcesManager />

      <Disclaimer />
    </div>
  );
}
