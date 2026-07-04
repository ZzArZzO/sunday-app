export interface BriefingSectionHeadingProps {
  number: string;
  title: string;
}

/** Section numeral set inside the heading text itself, not a floating pull-number. */
export function BriefingSectionHeading({ number, title }: BriefingSectionHeadingProps) {
  return (
    <h2 className="font-sans text-2xl font-semibold tracking-tight text-ink">
      <span className="mr-3 font-mono text-base font-normal tabular-nums text-ink-subtle">{number}</span>
      {title}
    </h2>
  );
}
