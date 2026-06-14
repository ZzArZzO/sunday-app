import type { BriefingResponse, BriefingSection } from "@/lib/types";
import { ConcentrationCard } from "@/components/ConcentrationCard";
import { Disclaimer } from "@/components/Disclaimer";
import { Sparkline } from "@/components/Sparkline";
import { formatDual, formatPct } from "@/lib/format";

/** Safely pull a numeric `spark` series out of a section's loosely-typed data. */
function sparkSeries(data: Record<string, unknown> | null): number[] | null {
  const raw = data?.spark;
  if (!Array.isArray(raw)) return null;
  const nums = raw.filter((v): v is number => typeof v === "number");
  return nums.length >= 2 ? nums : null;
}

/**
 * Modern briefing layout: dateline header, oversized net-worth hero, narrative
 * sections rendered as separated content blocks. Sans throughout with mono for
 * figures. Reads like a Linear changelog or Stripe Sessions recap — calm,
 * confident, contemporary.
 */
export function BriefingView({ briefing }: { briefing: BriefingResponse }) {
  const wow = Number(briefing.wow_delta.eur);
  const wowClass =
    wow > 0 ? "text-positive" : wow < 0 ? "text-negative" : "text-ink-muted";
  const wowSign = wow > 0 ? "+" : "";

  return (
    <article className="space-y-12 fade-up">
      <header className="space-y-2">
        <p className="label">Sunday briefing · week of {briefing.week_of}</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          The one number that matters
        </h1>
      </header>

      <section className="card p-8">
        <p className="label">Net worth</p>
        <p className="mt-3 font-sans text-5xl font-semibold leading-none tracking-tighter text-ink sm:text-6xl">
          {formatDual(briefing.net_worth)}
        </p>
        <p className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-base text-ink-muted">
          {briefing.wow_available ? (
            <>
              <span className="inline-flex items-center gap-1.5">
                <TrendIcon up={wow > 0} flat={wow === 0} className={wowClass} />
                <span className={`font-mono tabular-nums ${wowClass}`}>
                  {wowSign}
                  {formatPct(briefing.wow_delta_pct)}
                </span>
              </span>
              <span className="text-ink-subtle">·</span>
              <span className={`font-mono tabular-nums ${wowClass}`}>
                {wowSign}
                {formatDual(briefing.wow_delta)}
              </span>
              {briefing.wow_baseline_date ? (
                <>
                  <span className="text-ink-subtle">·</span>
                  <span className="text-ink-subtle">since {briefing.wow_baseline_date}</span>
                </>
              ) : null}
            </>
          ) : (
            <span className="text-ink-subtle">Week-over-week starts once your history builds</span>
          )}
          <span className="text-ink-subtle">·</span>
          <span className="text-ink-subtle">
            EUR/USD <span className="font-mono">{Number(briefing.fx_eur_usd).toFixed(4)}</span>
          </span>
        </p>
      </section>

      {briefing.sections
        .filter((s) => s.kind !== "headline")
        .map((section, idx) => (
          <SectionBlock key={`${section.kind}-${idx}`} section={section} />
        ))}

      {briefing.concentration_alerts.length > 0 ? (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-negative" />
            <p className="label text-negative">Alert · concentration</p>
          </div>
          <h2 className="font-sans text-2xl font-semibold tracking-tight">
            Above your thresholds this week
          </h2>
          <ConcentrationCard items={briefing.concentration_alerts} />
        </section>
      ) : null}

      <footer className="space-y-4 border-t border-rule pt-8">
        <p className="label">— end of briefing —</p>
        <Disclaimer
          extra={`Generated ${new Date(briefing.generated_at).toLocaleString()} · placeholder data for MVP preview.`}
        />
      </footer>
    </article>
  );
}

function SectionBlock({ section }: { section: BriefingSection }) {
  const spark = sparkSeries(section.data);
  return (
    <section className="space-y-3">
      <p className="label">{kindLabel(section.kind)}</p>
      <div className="flex items-start justify-between gap-4">
        <h2 className="font-sans text-2xl font-semibold tracking-tight text-ink">
          {section.title}
        </h2>
        {spark ? <Sparkline values={spark} className="mt-1 flex-none" /> : null}
      </div>
      <div className="max-w-prose whitespace-pre-line text-base leading-relaxed text-ink-muted">
        {section.body_markdown}
      </div>
    </section>
  );
}

function kindLabel(kind: string): string {
  switch (kind) {
    case "what_changed":
      return "This week";
    case "concentration":
      return "Concentration";
    case "regime":
      return "Regime";
    case "tax_flags":
      return "Tax";
    case "movers":
      return "Movers";
    default:
      return kind;
  }
}

function TrendIcon({
  up,
  flat,
  className = "",
}: {
  up: boolean;
  flat: boolean;
  className?: string;
}) {
  if (flat) {
    return (
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        width="14"
        height="14"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        className={className}
      >
        <path d="M5 12h14" />
      </svg>
    );
  }
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      width="14"
      height="14"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {up ? (
        <path d="M7 17l5-5 5 5M7 11l5-5 5 5" />
      ) : (
        <path d="M7 7l5 5 5-5M7 13l5 5 5-5" />
      )}
    </svg>
  );
}
