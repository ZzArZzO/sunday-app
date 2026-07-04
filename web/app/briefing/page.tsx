"use client";

import { BriefingColophon } from "@/components/BriefingColophon";
import { BriefingMasthead } from "@/components/BriefingMasthead";
import { BriefingSectionHeading } from "@/components/BriefingSectionHeading";
import { GainLossTag } from "@/components/GainLossTag";
import { MarkdownLite } from "@/components/MarkdownLite";
import { fetchBriefing } from "@/lib/api";
import { formatEurWhole, formatSignedPct, formatUsdApprox } from "@/lib/moneyFormat";
import { useAsync } from "@/lib/useAsync";
import type { BriefingResponse } from "@/lib/types";

const WORDS_PER_MINUTE = 200;

function estimateReadMinutes(briefing: BriefingResponse): number {
  const words = briefing.sections.reduce(
    (sum, section) => sum + section.body_markdown.split(/\s+/).filter(Boolean).length,
    0,
  );
  return Math.max(1, Math.round(words / WORDS_PER_MINUTE));
}

function formatGeneratedAt(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function BriefingPage() {
  const { data: briefing, loading, error } = useAsync(fetchBriefing);

  if (loading) {
    return (
      <div className="mx-auto max-w-prose space-y-6">
        <div className="skeleton h-12 w-1/2" />
        <div className="skeleton h-40 w-full" />
      </div>
    );
  }

  if (error || !briefing) {
    return (
      <div className="card border-negative/30 bg-negative-subtle/40 p-5">
        <p className="font-medium text-negative">Couldn&apos;t load briefing</p>
        <p className="mt-2 text-sm text-ink">{error}</p>
      </div>
    );
  }

  const netWorthEur = Number(briefing.net_worth.eur);
  const netWorthUsd = Number(briefing.net_worth.usd);
  const wowPct = Number(briefing.wow_delta_pct);

  return (
    <article className="mx-auto max-w-prose space-y-10 fade-up">
      <BriefingMasthead weekOf={briefing.week_of} readMinutes={estimateReadMinutes(briefing)} />

      <section className="space-y-4">
        <p className="font-sans text-6xl font-semibold leading-none tracking-tighter text-ink sm:text-7xl">
          {formatEurWhole(netWorthEur)}
        </p>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          {briefing.wow_available ? (
            <GainLossTag
              value={wowPct}
              size="lg"
              label={`${formatSignedPct(wowPct)} since last Sunday`}
            />
          ) : (
            <span className="text-sm text-ink-subtle">
              Week-over-week will appear once there&apos;s a prior week to compare against.
            </span>
          )}
          <span className="font-mono text-sm tabular-nums text-ink-subtle">
            {formatUsdApprox(netWorthUsd)}
          </span>
        </div>
      </section>

      <div className="divide-y divide-rule border-t border-rule">
        {briefing.sections.map((section, i) => (
          <section key={section.kind} className="space-y-4 py-8 first:pt-0 last:pb-0">
            <BriefingSectionHeading number={String(i + 1).padStart(2, "0")} title={section.title} />
            <div className="space-y-4 text-base leading-relaxed text-ink-muted">
              <MarkdownLite markdown={section.body_markdown} />
            </div>
          </section>
        ))}
      </div>

      <BriefingColophon
        generatedAt={formatGeneratedAt(briefing.generated_at)}
        fxEurUsd={Number(briefing.fx_eur_usd)}
      />
    </article>
  );
}
