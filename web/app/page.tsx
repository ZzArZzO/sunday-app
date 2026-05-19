import Link from "next/link";

import { Disclaimer } from "@/components/Disclaimer";

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <p className="text-sm uppercase tracking-wide text-ink-subtle">
          Sunday · MVP preview
        </p>
        <h1 className="text-4xl font-semibold leading-tight">
          A 5-minute portfolio briefing,
          <br />
          every Sunday evening.
        </h1>
        <p className="max-w-2xl text-lg text-ink-muted">
          For self-directed EU retail investors who hold stocks <em>and</em> crypto.
          Privacy-first — no wallet-connect, no chain reads, no broker API permissions.
        </p>
        <div className="flex gap-3">
          <Link
            href="/upload"
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
          >
            Upload a CSV
          </Link>
          <Link
            href="/briefing"
            className="rounded-md border border-ink/10 px-4 py-2 text-sm font-medium hover:bg-ink/5"
          >
            See a sample briefing
          </Link>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        <Feature
          title="One number that matters"
          body="Net worth EUR + USD, week-over-week delta. No more four-tab Sunday math."
        />
        <Feature
          title="Concentration you can see"
          body="Single-name and sector thresholds you configure. Alerts before exposure becomes a problem."
        />
        <Feature
          title="Regime context, not advice"
          body="Risk-on / risk-off, cycle position, crypto-cycle indicator. Informational. Always."
        />
      </section>

      <Disclaimer extra="MVP preview. No real prices yet — sample portfolio uses placeholder values." />
    </div>
  );
}

function Feature({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-ink/10 bg-paper-card p-5">
      <h3 className="font-medium">{title}</h3>
      <p className="mt-2 text-sm text-ink-muted">{body}</p>
    </div>
  );
}
