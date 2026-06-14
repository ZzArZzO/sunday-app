import { formatDateTime } from "@/lib/format";

// "Show your work" trust strip. The category's biggest trust-killer is numbers
// that don't reconcile, so we state plainly how fresh the data is and how many
// holdings are valued at live price vs. falling back to cost basis.

type DataQualityNoteProps = {
  asOf: string;
  priced: number;
  total: number;
  fxEurUsd: string;
};

export function DataQualityNote({ asOf, priced, total, fxEurUsd }: DataQualityNoteProps) {
  const unpriced = Math.max(0, total - priced);
  const allLive = total > 0 && unpriced === 0;

  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-ink-subtle">
      <span
        aria-hidden
        className={`inline-block h-1.5 w-1.5 flex-none rounded-full ${
          allLive ? "bg-positive" : "bg-warn"
        }`}
      />
      <span>Prices as of {formatDateTime(asOf)}</span>
      <span>·</span>
      {total > 0 ? (
        <span>
          <span className="font-mono tabular-nums text-ink-muted">
            {priced}/{total}
          </span>{" "}
          holdings at live price
          {unpriced > 0 ? (
            <span className="text-ink-subtle">
              , {unpriced} valued at cost basis
            </span>
          ) : null}
        </span>
      ) : (
        <span>No holdings yet</span>
      )}
      <span>·</span>
      <span>
        EUR/USD <span className="font-mono tabular-nums">{Number(fxEurUsd).toFixed(4)}</span>
      </span>
    </p>
  );
}
