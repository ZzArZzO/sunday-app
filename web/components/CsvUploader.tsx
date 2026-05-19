"use client";

import { useRef, useState } from "react";

import { uploadCsv } from "@/lib/api";
import type { IngestResult } from "@/lib/types";

type Status =
  | { kind: "idle" }
  | { kind: "uploading" }
  | { kind: "done"; result: IngestResult }
  | { kind: "error"; message: string };

export function CsvUploader() {
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setStatus({ kind: "uploading" });
    try {
      const result = await uploadCsv(file);
      setStatus({ kind: "done", result });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setStatus({ kind: "error", message });
    }
  }

  function onChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) void handleFile(file);
  }

  function onDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void handleFile(file);
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
          ${status.kind === "uploading" ? "opacity-60" : ""}`}
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
          We read position rows and discard everything else. PII columns are never parsed.
        </p>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={status.kind === "uploading"}
          className="btn btn-primary mt-6"
        >
          {status.kind === "uploading" ? "Uploading…" : "Choose file"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={onChange}
          disabled={status.kind === "uploading"}
          className="sr-only"
        />
      </div>

      {status.kind === "error" ? (
        <div
          role="alert"
          className="rounded-md border border-negative/30 bg-negative-subtle/40 p-4 text-sm"
        >
          <p className="font-medium text-negative">Upload failed</p>
          <p className="mt-1 text-ink">{status.message}</p>
        </div>
      ) : null}

      {status.kind === "done" ? (
        <div
          role="status"
          aria-live="polite"
          className="rounded-md border border-positive/30 bg-positive-subtle/40 p-4 text-sm"
        >
          <p className="font-medium text-positive">Imported.</p>
          <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 font-mono text-ink">
            <Row k="Rows read" v={status.result.rows_read} />
            <Row k="Positions created" v={status.result.positions_created} />
            <Row k="Positions updated" v={status.result.positions_updated} />
            <Row k="Lots created" v={status.result.lots_created} />
          </dl>
          {status.result.warnings.length > 0 ? (
            <details className="mt-3">
              <summary className="cursor-pointer text-ink-muted">
                {status.result.warnings.length} warning(s)
              </summary>
              <ul className="mt-2 list-disc pl-6 text-ink-muted">
                {status.result.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      ) : null}
    </div>
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
