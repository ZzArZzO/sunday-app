/**
 * Persistent legal disclaimer. Card-style note with an info dot — visible but
 * not noisy. Used wherever portfolio data or LLM narrative appears.
 */
export function Disclaimer({ extra }: { extra?: string }) {
  return (
    <aside
      role="note"
      className="flex gap-3 rounded-md border border-rule bg-surface-2/60 p-4 text-xs leading-relaxed text-ink-muted"
    >
      <span
        aria-hidden
        className="mt-1 inline-flex h-1.5 w-1.5 flex-none rounded-full bg-accent"
      />
      <div className="space-y-1">
        <p className="text-ink">
          Sunday is information, not investment advice. Numbers are deterministic; narrative is
          generated with AI and filtered for compliance with EU rules on personal recommendations.
        </p>
        {extra ? <p className="text-ink-subtle">{extra}</p> : null}
      </div>
    </aside>
  );
}
