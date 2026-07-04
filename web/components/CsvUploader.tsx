"use client";

import { useRef, useState } from "react";

import { previewCsv, refreshPrices, uploadCsv } from "@/lib/api";
import type { IngestPreviewResponse, IngestResult, PreviewRowView, PriceRefreshResponse } from "@/lib/types";

// Import wizard: Upload → Review (detected format, column mapping, per-row
// status with skipped-row reasons) → Confirm. The preview never writes; confirm
// reuses the existing /api/ingest endpoint. A freshly-imported position has no
// price yet, so confirm also triggers a price refresh before showing "done" —
// otherwise the dashboard would silently show cost basis dressed up as a
// current value until someone happens to find the manual refresh button.
type State =
  | { kind: "idle" }
  | { kind: "previewing" }
  | { kind: "preview"; file: File; preview: IngestPreviewResponse }
  | { kind: "importing"; preview: IngestPreviewResponse }
  | { kind: "pricing"; result: IngestResult }
  | { kind: "done"; result: IngestResult; priceRefresh: PriceRefreshResponse | null }
  | { kind: "error"; message: string };

export function CsvUploader({ broker }: { broker?: string }) {
  const [state, setState] = useState<State>({ kind: "idle" });
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setState({ kind: "previewing" });
    try {
      const preview = await previewCsv(file);
      setState({ kind: "preview", file, preview });
    } catch (err) {
      setState({ kind: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  async function confirmImport(file: File, preview: IngestPreviewResponse) {
    setState({ kind: "importing", preview });
    let result: IngestResult;
    try {
      result = await uploadCsv(file, broker);
    } catch (err) {
      setState({ kind: "error", message: err instanceof Error ? err.message : String(err) });
      return;
    }

    // The import itself succeeded regardless of what happens next — a price
    // refresh failure (rate limit, a symbol Yahoo doesn't carry) shouldn't be
    // reported as the import having failed.
    setState({ kind: "pricing", result });
    let priceRefresh: PriceRefreshResponse | null = null;
    try {
      priceRefresh = await refreshPrices();
    } catch {
      priceRefresh = null;
    }
    setState({ kind: "done", result, priceRefresh });
  }

  function reset() {
    setState({ kind: "idle" });
  }

  function onDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void handleFile(file);
  }

  if (state.kind === "preview") {
    return (
      <PreviewStep
        preview={state.preview}
        onCancel={reset}
        onConfirm={() => void confirmImport(state.file, state.preview)}
      />
    );
  }

  if (state.kind === "importing") {
    return <p className="card p-6 text-sm text-ink-muted">Importing {state.preview.ok_count} rows…</p>;
  }

  if (state.kind === "pricing") {
    return <p className="card p-6 text-sm text-ink-muted">Imported. Fetching current prices…</p>;
  }

  if (state.kind === "done") {
    return <DoneStep result={state.result} priceRefresh={state.priceRefresh} onReset={reset} />;
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`group relative flex flex-col items-center justify-center rounded-lg border border-dashed bg-surface px-8 py-14 text-center transition-all duration-200 ease-out
          ${dragging ? "border-accent bg-accent-subtle/40" : "border-rule hover:border-ink-subtle"}
          ${state.kind === "previewing" ? "opacity-60" : ""}`}
      >
        <span
          aria-hidden
          className={`inline-flex h-12 w-12 items-center justify-center rounded-full bg-surface-2 text-ink-muted transition-colors group-hover:text-ink ${
            dragging ? "bg-accent text-accent-fg" : ""
          }`}
        >
          <UploadIcon />
        </span>
        <p className="mt-4 text-base font-semibold text-ink">Drop a CSV, or browse</p>
        <p className="mt-1 max-w-prose text-sm text-ink-muted">
          You&apos;ll see exactly what we parsed — and what we skip — before anything is imported.
          PII columns are never read.
        </p>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={state.kind === "previewing"}
          className="btn btn-primary mt-6"
        >
          {state.kind === "previewing" ? "Reading…" : "Choose file"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
          }}
          disabled={state.kind === "previewing"}
          className="sr-only"
        />
      </div>

      {state.kind === "error" ? (
        <div role="alert" className="rounded-md border border-negative/30 bg-negative-subtle/40 p-4 text-sm">
          <p className="font-medium text-negative">Couldn&apos;t read that file</p>
          <p className="mt-1 text-ink">{state.message}</p>
        </div>
      ) : null}
    </div>
  );
}

function PreviewStep({
  preview,
  onCancel,
  onConfirm,
}: {
  preview: IngestPreviewResponse;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const [onlySkipped, setOnlySkipped] = useState(false);
  const rows = onlySkipped ? preview.rows.filter((r) => r.status === "skipped") : preview.rows;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="label">Review · detected {preview.detected_format.replace("_", " ")}</p>
          <p className="mt-1 text-sm text-ink">
            <span className="font-mono text-positive">{preview.ok_count}</span> rows ready
            {preview.skipped_count > 0 ? (
              <>
                {" · "}
                <span className="font-mono text-warn">{preview.skipped_count}</span> skipped
              </>
            ) : null}
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={onCancel} className="btn btn-ghost">
            Cancel
          </button>
          <button type="button" onClick={onConfirm} className="btn btn-primary" disabled={preview.ok_count === 0}>
            Import {preview.ok_count} rows
          </button>
        </div>
      </div>

      <div className="card p-4">
        <p className="label">Column mapping</p>
        <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
          {preview.columns.map((c) => (
            <li key={c.source} className="flex items-center gap-1.5">
              <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-positive" />
              <span className="text-ink-muted">{c.source}</span>
              <span className="text-ink-subtle">→</span>
              <span className="font-medium text-ink">{c.mapped_to}</span>
              {c.sample ? <span className="font-mono text-xs text-ink-subtle">e.g. {c.sample}</span> : null}
            </li>
          ))}
        </ul>
        {preview.unmapped_headers.length > 0 ? (
          <p className="mt-2 text-xs text-ink-subtle">
            Ignored columns: {preview.unmapped_headers.join(", ")}
          </p>
        ) : null}
      </div>

      {preview.skipped_count > 0 ? (
        <label className="flex items-center gap-2 text-sm text-ink-muted">
          <input
            type="checkbox"
            checked={onlySkipped}
            onChange={(e) => setOnlySkipped(e.target.checked)}
            className="accent-accent"
          />
          Show only skipped rows
        </label>
      ) : null}

      <div className="card overflow-hidden">
        <div className="max-h-[360px] overflow-auto">
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 bg-surface-2/80">
              <tr className="border-b border-rule text-left">
                <Th>Line</Th>
                <Th>Status</Th>
                <Th>Date</Th>
                <Th>Type</Th>
                <Th>Ticker</Th>
                <Th align="right">Qty</Th>
                <Th align="right">Price</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <RowView key={r.line} row={r} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {preview.warnings.length > 0 ? (
        <ul className="space-y-1 text-xs text-ink-subtle">
          {preview.warnings.map((w) => (
            <li key={w}>· {w}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function RowView({ row }: { row: PreviewRowView }) {
  const skipped = row.status === "skipped";
  return (
    <tr className={`border-b border-rule last:border-0 ${skipped ? "bg-warn-subtle/20" : ""}`}>
      <Td mono>{row.line}</Td>
      <Td>
        {skipped ? (
          <span className="inline-flex items-center gap-1 text-warn" title={row.reason ?? undefined}>
            <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-warn" />
            skipped
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-positive">
            <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-positive" />
            ok
          </span>
        )}
      </Td>
      {skipped ? (
        <td className="px-3 py-2 text-xs text-ink-subtle" colSpan={5}>
          {row.reason}
        </td>
      ) : (
        <>
          <Td mono>{row.date}</Td>
          <Td>{row.kind}</Td>
          <Td>{row.ticker}</Td>
          <Td align="right" mono>
            {row.quantity}
          </Td>
          <Td align="right" mono>
            {row.unit_price_eur}
          </Td>
        </>
      )}
    </tr>
  );
}

function DoneStep({
  result,
  priceRefresh,
  onReset,
}: {
  result: IngestResult;
  priceRefresh: PriceRefreshResponse | null;
  onReset: () => void;
}) {
  return (
    <div className="space-y-4">
      <div role="status" aria-live="polite" className="rounded-md border border-positive/30 bg-positive-subtle/40 p-4 text-sm">
        <p className="font-medium text-positive">Imported.</p>
        <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 font-mono text-ink">
          <Row k="Rows read" v={result.rows_read} />
          <Row k="Positions created" v={result.positions_created} />
          <Row k="Positions updated" v={result.positions_updated} />
          <Row k="Lots created" v={result.lots_created} />
        </dl>
        {result.warnings.length > 0 ? (
          <div className="mt-3 rounded-md border border-warn/30 bg-warn-subtle/40 p-3">
            <p className="font-medium text-warn">Notes</p>
            <ul className="mt-1 list-disc pl-6 text-ink-muted">
              {result.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>

      {priceRefresh ? (
        <div className="rounded-md border border-rule bg-surface-2/50 p-4 text-sm">
          <p className="font-medium text-ink">
            {priceRefresh.priced} of {priceRefresh.total} holding{priceRefresh.total === 1 ? "" : "s"} priced
          </p>
          {priceRefresh.unpriced > 0 ? (
            <p className="mt-1 text-ink-muted">
              {priceRefresh.unpriced} couldn&apos;t be priced right now — some instruments (exotic
              certificates, thinly-traded ETCs) aren&apos;t carried by our price data provider. Those
              show your cost basis until a price is found; you can retry anytime from the Dashboard.
            </p>
          ) : null}
        </div>
      ) : (
        <div className="rounded-md border border-warn/30 bg-warn-subtle/40 p-4 text-sm">
          <p className="font-medium text-warn">Couldn&apos;t fetch prices just now</p>
          <p className="mt-1 text-ink-muted">
            Your import succeeded, but the price refresh didn&apos;t go through. Your holdings will
            show cost basis until you retry — tap Refresh Prices on the Dashboard.
          </p>
        </div>
      )}

      <button type="button" onClick={onReset} className="btn btn-ghost">
        Import another file
      </button>
    </div>
  );
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return <th className={`label px-3 py-2 ${align === "right" ? "text-right" : "text-left"}`}>{children}</th>;
}

function Td({
  children,
  align = "left",
  mono = false,
}: {
  children: React.ReactNode;
  align?: "left" | "right";
  mono?: boolean;
}) {
  return (
    <td
      className={`px-3 py-2 ${align === "right" ? "text-right" : "text-left"} ${
        mono ? "font-mono text-ink" : "text-ink"
      }`}
    >
      {children}
    </td>
  );
}

function Row({ k, v }: { k: string; v: number }) {
  return (
    <>
      <dt className="text-ink-muted">{k}</dt>
      <dd className="text-right text-ink">{v}</dd>
    </>
  );
}

function UploadIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 3v12M7 8l5-5 5 5M5 21h14" />
    </svg>
  );
}
