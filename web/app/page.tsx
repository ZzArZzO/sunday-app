import Link from "next/link";

import { Disclaimer } from "@/components/Disclaimer";

export default function HomePage() {
  return (
    <div className="space-y-20">
      <section className="relative -mx-6 overflow-hidden px-6 pb-12 pt-8 sm:pt-16">
        <div aria-hidden className="absolute inset-0 -z-10 grid-pattern" />
        <div className="space-y-8 fade-up">
          <span className="inline-flex items-center gap-2 rounded-md border border-rule bg-surface px-3 py-1 text-xs font-medium text-ink-muted shadow-soft">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
            Preview · early access
          </span>
          <h1 className="max-w-3xl font-sans text-5xl font-semibold leading-[1.05] tracking-tighter text-ink sm:text-6xl md:text-7xl">
            A quiet portfolio briefing,{" "}
            <span className="text-ink-subtle">every Sunday.</span>
          </h1>
          <p className="max-w-2xl text-lg leading-relaxed text-ink-muted">
            For self-directed European investors who hold stocks <em className="italic">and</em>{" "}
            crypto and want one calm read on a Sunday evening — not another dashboard you forget to
            open.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link href="/upload" className="btn btn-primary">
              Import a portfolio
              <ArrowRight />
            </Link>
            <Link href="/briefing" className="btn btn-ghost">
              See a sample briefing
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <FeatureCard
          step="01"
          title="One number that matters"
          body="Net worth in EUR and USD, week over week, and what changed since you last looked."
        />
        <FeatureCard
          step="02"
          title="Concentration you can see"
          body="Single-name and sector thresholds you configure. We surface what crossed — we don't tell you to act."
        />
        <FeatureCard
          step="03"
          title="Regime, not recommendations"
          body="Macro context, cycle position, crypto-cycle signal. Always informational, never advisory."
        />
      </section>

      <section className="card p-8">
        <p className="label mb-3">A note on what this is, and isn't</p>
        <p className="max-w-prose text-base leading-relaxed text-ink-muted">
          Sunday reads your portfolio data only — no wallet-connect, no chain reads, no broker
          permissions. Crypto holdings are declared by you. The briefing is delivered as a web
          view, an email, and a PDF, every Sunday evening in your timezone.
        </p>
        <div className="mt-6">
          <Disclaimer extra="MVP preview · sample portfolio uses placeholder prices · live prices land in Phase 2." />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({
  step,
  title,
  body,
}: {
  step: string;
  title: string;
  body: string;
}) {
  return (
    <article className="group card p-6 transition-all duration-200 ease-out hover:-translate-y-0.5 hover:shadow-elev">
      <div className="flex items-baseline justify-between">
        <span className="label">{step}</span>
        <ArrowUpRight className="text-ink-subtle transition-colors group-hover:text-accent" />
      </div>
      <h3 className="mt-6 font-sans text-lg font-semibold tracking-tight text-ink">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-ink-muted">{body}</p>
    </article>
  );
}

function ArrowRight() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14M13 5l7 7-7 7" />
    </svg>
  );
}

function ArrowUpRight({ className = "" }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M7 17L17 7M9 7h8v8" />
    </svg>
  );
}
