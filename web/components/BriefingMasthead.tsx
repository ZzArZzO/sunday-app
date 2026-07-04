import type { BriefingIssue } from "@/lib/briefingSnapshot";

export interface BriefingMastheadProps {
  issue: BriefingIssue;
}

/**
 * The letter's own masthead — distinct from the app's persistent top nav.
 * Signals "this is a numbered edition," the way a newsletter's header does,
 * rather than another app screen.
 */
export function BriefingMasthead({ issue }: BriefingMastheadProps) {
  return (
    <header className="space-y-4 border-b border-rule pb-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <span className="font-sans text-base font-semibold tracking-tight text-ink">Sunday</span>
        <p className="font-mono text-xs tabular-nums text-ink-subtle">
          Week of {issue.weekOf} · Issue {issue.issueNumber} · {issue.readMinutes} min read
        </p>
      </div>
      <p className="text-sm text-ink-subtle">{issue.dateline}</p>
    </header>
  );
}
