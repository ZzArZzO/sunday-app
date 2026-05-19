"use client";

import { useState } from "react";

import { uploadCsv } from "@/lib/api";
import type { IngestResult } from "@/lib/types";

type Status =
  | { kind: "idle" }
  | { kind: "uploading" }
  | { kind: "done"; result: IngestResult }
  | { kind: "error"; message: string };

export function CsvUploader() {
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function onChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setStatus({ kind: "uploading" });
    try {
      const result = await uploadCsv(file);
      setStatus({ kind: "done", result });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setStatus({ kind: "error", message });
    }
  }

  return (
    <div className="space-y-4">
      <label className="block">
        <span className="block text-sm font-medium mb-2">Trade Republic CSV</span>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={onChange}
          disabled={status.kind === "uploading"}
          className="block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:bg-accent file:px-4 file:py-2 file:text-white file:hover:bg-blue-600"
        />
      </label>

      {status.kind === "uploading" ? (
        <p className="text-sm text-ink-muted">Uploading and parsing…</p>
      ) : null}

      {status.kind === "error" ? (
        <p className="text-sm text-negative">{status.message}</p>
      ) : null}

      {status.kind === "done" ? (
        <div className="rounded-md border border-positive/30 bg-positive/5 p-4 text-sm">
          <p className="font-medium text-positive">Imported.</p>
          <ul className="mt-2 space-y-1 text-ink-muted">
            <li>Rows read: {status.result.rows_read}</li>
            <li>Positions created: {status.result.positions_created}</li>
            <li>Positions updated: {status.result.positions_updated}</li>
            <li>Lots created: {status.result.lots_created}</li>
          </ul>
          {status.result.warnings.length > 0 ? (
            <details className="mt-3">
              <summary className="cursor-pointer text-ink-muted">
                {status.result.warnings.length} warning(s)
              </summary>
              <ul className="mt-2 list-disc pl-6">
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
