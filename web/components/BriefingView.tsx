import type { BriefingResponse, BriefingSection } from "@/lib/types";
import { ConcentrationCard } from "@/components/ConcentrationCard";
import { Disclaimer } from "@/components/Disclaimer";
import { formatDual, formatPct } from "@/lib/format";

function SectionBlock({ section }: { section: BriefingSection }) {
  return (
    <section className="rounded-lg border border-ink/10 bg-paper-card p-6">
      <h3 className="text-lg font-semibold">{section.title}</h3>
      <div className="mt-2 whitespace-pre-line text-sm text-ink-muted">
        {section.body_markdown}
      </div>
    </section>
  );
}

export function BriefingView({ briefing }: { briefing: BriefingResponse }) {
  return (
    <article className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-wide text-ink-subtle">
          Sunday briefing — week of {briefing.week_of}
        </p>
        <h2 className="text-3xl font-semibold">{formatDual(briefing.net_worth)}</h2>
        <p className="text-sm text-ink-muted">
          Week over week: {formatPct(briefing.wow_delta_pct)} ({formatDual(briefing.wow_delta)}) · FX
          EUR/USD {Number(briefing.fx_eur_usd).toFixed(4)}
        </p>
      </header>

      {briefing.sections.map((section, idx) => (
        <SectionBlock key={`${section.kind}-${idx}`} section={section} />
      ))}

      {briefing.concentration_alerts.length > 0 ? (
        <section className="rounded-lg border border-ink/10 bg-paper-card p-6">
          <h3 className="text-lg font-semibold">Concentration alerts</h3>
          <div className="mt-3">
            <ConcentrationCard items={briefing.concentration_alerts} />
          </div>
        </section>
      ) : null}

      <footer className="border-t border-ink/10 pt-4">
        <Disclaimer
          extra={`Generated ${new Date(briefing.generated_at).toLocaleString()}`}
        />
      </footer>
    </article>
  );
}
