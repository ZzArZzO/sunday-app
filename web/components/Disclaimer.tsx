/**
 * Persistent legal disclaimer. Rendered on every screen that shows portfolio
 * data or any LLM-generated narrative. See docs/LEGAL.md for the reasoning.
 */
export function Disclaimer({ extra }: { extra?: string }) {
  return (
    <p className="text-xs text-ink-muted">
      Not investment advice. Information only.{" "}
      <span className="text-ink-subtle">Generated with AI assistance.</span>
      {extra ? <span className="block mt-1 text-ink-subtle">{extra}</span> : null}
    </p>
  );
}
