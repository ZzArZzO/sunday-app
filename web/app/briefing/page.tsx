import { BriefingColophon } from "@/components/BriefingColophon";
import { BriefingMasthead } from "@/components/BriefingMasthead";
import { BriefingSectionHeading } from "@/components/BriefingSectionHeading";
import { GainLossTag } from "@/components/GainLossTag";
import { BRIEFING_ISSUE } from "@/lib/briefingSnapshot";
import { formatEurWhole, formatSignedEurWhole, formatSignedPct, formatUsdApprox } from "@/lib/moneyFormat";
import { CONCENTRATION_SNAPSHOT, HOLDINGS_SNAPSHOT, PORTFOLIO_SNAPSHOT } from "@/lib/portfolioSnapshot";

const [vwce, sxr8, asml, btc] = HOLDINGS_SNAPSHOT;

export default function BriefingPage() {
  return (
    <article className="mx-auto max-w-prose space-y-10 fade-up">
      <BriefingMasthead issue={BRIEFING_ISSUE} />

      <section className="space-y-4">
        <p className="font-sans text-6xl font-semibold leading-none tracking-tighter text-ink sm:text-7xl">
          {formatEurWhole(PORTFOLIO_SNAPSHOT.netWorthEur)}
        </p>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <GainLossTag
            value={PORTFOLIO_SNAPSHOT.weekChangePct}
            size="lg"
            label={`${formatSignedPct(PORTFOLIO_SNAPSHOT.weekChangePct)} since last Sunday`}
          />
          <span className="font-mono text-sm tabular-nums text-ink-subtle">
            {formatUsdApprox(PORTFOLIO_SNAPSHOT.netWorthUsdApprox)}
          </span>
        </div>
        <p className="text-lg leading-relaxed text-ink-muted">
          Your portfolio added {formatSignedEurWhole(PORTFOLIO_SNAPSHOT.weekChangeEur)} this week, largely on
          continued strength in crypto and broad equities. Tech concentration remains above the threshold
          you set — noted below, not acted on.
        </p>
      </section>

      <div className="divide-y divide-rule border-t border-rule">
        <section className="space-y-4 py-8 first:pt-0">
          <BriefingSectionHeading number="01" title="What changed" />
          <p className="text-base leading-relaxed text-ink-muted">
            Two positions did the heavy lifting since you opened them: {btc.name}, up{" "}
            <GainLossTag value={btc.pnlPct} label={formatSignedPct(btc.pnlPct)} className="mx-0.5" />, and
            your {vwce.name} tracker, up{" "}
            <GainLossTag value={vwce.pnlPct} label={formatSignedPct(vwce.pnlPct)} className="mx-0.5" />. The{" "}
            {sxr8.name} fund added{" "}
            <GainLossTag value={sxr8.pnlPct} label={formatSignedPct(sxr8.pnlPct)} className="mx-0.5" />.{" "}
            {asml.name} is the one exception, down{" "}
            <GainLossTag value={asml.pnlPct} label={formatSignedPct(asml.pnlPct)} className="mx-0.5" /> from
            cost, though it&apos;s a comparatively small slice of the book.
          </p>
          <p className="text-base leading-relaxed text-ink-muted">
            Altogether, the portfolio is sitting{" "}
            <GainLossTag
              value={PORTFOLIO_SNAPSHOT.totalPnlPct}
              label={formatSignedPct(PORTFOLIO_SNAPSHOT.totalPnlPct)}
              className="mx-0.5"
            />{" "}
            ahead of what you&apos;ve put in — and{" "}
            <GainLossTag
              value={PORTFOLIO_SNAPSHOT.weekChangePct}
              label={formatSignedPct(PORTFOLIO_SNAPSHOT.weekChangePct)}
              className="mx-0.5"
            />{" "}
            of that showed up just this week, worth {formatEurWhole(PORTFOLIO_SNAPSHOT.weekChangeEur)}.
          </p>
        </section>

        <section className="space-y-4 py-8">
          <BriefingSectionHeading number="02" title="Concentration" />
          <p className="text-base leading-relaxed text-ink-muted">
            {CONCENTRATION_SNAPSHOT.label} now makes up{" "}
            <span className="font-mono tabular-nums text-ink">{CONCENTRATION_SNAPSHOT.weightPct}%</span> of
            the portfolio — {CONCENTRATION_SNAPSHOT.weightPct - CONCENTRATION_SNAPSHOT.thresholdPct} points
            above the{" "}
            <span className="font-mono tabular-nums text-ink">{CONCENTRATION_SNAPSHOT.thresholdPct}%</span>{" "}
            guideline you set for yourself. That&apos;s simple arithmetic, not a nudge to sell anything —
            Sunday describes the shape of your book, it doesn&apos;t tell you what to do with it.
          </p>
          <p className="text-base leading-relaxed text-ink-muted">
            Both {vwce.name} and {asml.name} carry meaningful tech exposure, so a rough week for the sector
            would land harder here than elsewhere in the portfolio.
          </p>
        </section>

        <section className="space-y-4 py-8 last:pb-0">
          <BriefingSectionHeading number="03" title="The week ahead" />
          <p className="text-base leading-relaxed text-ink-muted">
            Nothing on the calendar changes the shape of this portfolio before next Sunday — no earnings, no
            dividend dates, and no thresholds crossed beyond the one above. If that changes, it&apos;ll show
            up here first, not as a push notification mid-week.
          </p>
        </section>
      </div>

      <BriefingColophon generatedAt={BRIEFING_ISSUE.generatedAt} fxEurUsd={PORTFOLIO_SNAPSHOT.fxEurUsd} />
    </article>
  );
}
