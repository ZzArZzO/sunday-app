import { GainLossTag } from "@/components/GainLossTag";
import { formatSignedEurWhole, formatSignedPct } from "@/lib/moneyFormat";
import { CONCENTRATION_SNAPSHOT, HOLDINGS_SNAPSHOT, PORTFOLIO_SNAPSHOT } from "@/lib/portfolioSnapshot";

const [vwce, , asml, btc] = HOLDINGS_SNAPSHOT;

/**
 * A worked example, grounded in the same portfolio the dashboard and
 * briefing use — so a first-time visitor sees what a real answer looks like
 * before typing anything. Static, not part of the live thread: it never
 * reaches the chat API, so it can't leak fabricated turns into real history.
 */
export function AssistantExampleExchange() {
  return (
    <div className="card space-y-5 p-5">
      <p className="label">Example</p>

      <ExampleTurn
        question="What's my biggest concentration risk right now?"
        answer={
          <>
            {CONCENTRATION_SNAPSHOT.label} is your biggest concentration right now — it makes up{" "}
            <span className="font-mono tabular-nums text-ink">{CONCENTRATION_SNAPSHOT.weightPct}%</span> of
            the portfolio, {CONCENTRATION_SNAPSHOT.weightPct - CONCENTRATION_SNAPSHOT.thresholdPct} points
            above the{" "}
            <span className="font-mono tabular-nums text-ink">{CONCENTRATION_SNAPSHOT.thresholdPct}%</span>{" "}
            threshold you set. That&apos;s mostly coming from {vwce.name} and {asml.name}, both of which
            carry meaningful tech exposure. This describes your current allocation — it&apos;s not a signal
            to buy or sell anything.
          </>
        }
        facts={[
          `Tech weight: ${CONCENTRATION_SNAPSHOT.weightPct}% (threshold ${CONCENTRATION_SNAPSHOT.thresholdPct}%)`,
          `Largest tech contributors: ${vwce.ticker} ${vwce.weightPct}%, ${asml.ticker} ${asml.weightPct}%`,
        ]}
      />

      <ExampleTurn
        question="What changed in my portfolio this week?"
        answer={
          <>
            Your portfolio is up {formatSignedEurWhole(PORTFOLIO_SNAPSHOT.weekChangeEur)} this week, or{" "}
            <GainLossTag
              value={PORTFOLIO_SNAPSHOT.weekChangePct}
              label={formatSignedPct(PORTFOLIO_SNAPSHOT.weekChangePct)}
              className="mx-0.5"
            />
            — driven mainly by {btc.name}, up{" "}
            <GainLossTag value={btc.pnlPct} label={formatSignedPct(btc.pnlPct)} className="mx-0.5" /> since
            you opened the position, and continued strength in global equities. {asml.name} was the one
            holding to close lower, down{" "}
            <GainLossTag value={asml.pnlPct} label={formatSignedPct(asml.pnlPct)} className="mx-0.5" /> from
            cost. None of this changes your allocation targets — it&apos;s simply this week&apos;s move.
          </>
        }
        facts={[
          `Weekly change: ${formatSignedEurWhole(PORTFOLIO_SNAPSHOT.weekChangeEur)} (${formatSignedPct(
            PORTFOLIO_SNAPSHOT.weekChangePct,
          )})`,
          `Biggest mover: ${btc.ticker} ${formatSignedPct(btc.pnlPct)} since opened`,
        ]}
      />
    </div>
  );
}

function ExampleTurn({
  question,
  answer,
  facts,
}: {
  question: string;
  answer: React.ReactNode;
  facts: string[];
}) {
  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-ink px-4 py-2.5 text-sm leading-relaxed text-bg">
          {question}
        </p>
      </div>
      <div className="flex flex-col items-start gap-2">
        <p className="max-w-[85%] rounded-2xl rounded-bl-sm border border-rule bg-surface px-4 py-2.5 text-sm leading-relaxed text-ink">
          {answer}
        </p>
        <div className="max-w-[85%] space-y-1.5 rounded-md border border-rule bg-surface-2/50 px-3 py-2 text-xs text-ink-muted">
          <p className="text-ink-subtle">Based on your portfolio</p>
          <ul className="space-y-0.5">
            {facts.map((f) => (
              <li key={f} className="font-mono tabular-nums">
                {f}
              </li>
            ))}
          </ul>
          <p className="text-ink-subtle">These figures are computed server-side, not by the AI.</p>
        </div>
      </div>
    </div>
  );
}
