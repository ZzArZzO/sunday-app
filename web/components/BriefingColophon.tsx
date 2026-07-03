export interface BriefingColophonProps {
  generatedAt: string;
  fxEurUsd: number;
}

/**
 * Sign-off plus small print. Deliberately frameless — no card, no border box
 * — so the letter closes the way a letter does, not the way a dashboard
 * widget ends.
 */
export function BriefingColophon({ generatedAt, fxEurUsd }: BriefingColophonProps) {
  return (
    <footer className="space-y-6 pt-4">
      <p className="text-xl italic tracking-tight text-ink">See you next Sunday.</p>
      <div className="space-y-1 border-t border-rule pt-6 text-xs leading-relaxed text-ink-subtle">
        <p>
          Generated {generatedAt} · EUR/USD{" "}
          <span className="font-mono tabular-nums">{fxEurUsd.toFixed(4)}</span> · prices from your connected
          brokers and exchanges.
        </p>
        <p>Sunday is information, not investment advice; nothing here is a recommendation to buy, sell, or hold.</p>
      </div>
    </footer>
  );
}
