"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { refreshPrices } from "@/lib/api";

type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done"; priced: number; unpriced: number; live: boolean }
  | { kind: "error"; message: string };

/**
 * Fetches live prices + EUR/USD for the portfolio, then refreshes the server
 * component so the new numbers render. Honest about partial results: shows how
 * many holdings could be priced and warns if FX is still the placeholder.
 */
export function RefreshPricesButton() {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function run() {
    setStatus({ kind: "loading" });
    try {
      const res = await refreshPrices();
      setStatus({
        kind: "done",
        priced: res.priced,
        unpriced: res.unpriced,
        live: res.eur_usd_source !== "placeholder",
      });
      router.refresh();
    } catch (err) {
      setStatus({ kind: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={run}
        disabled={status.kind === "loading"}
        className="btn btn-ghost"
      >
        {status.kind === "loading" ? "Refreshing…" : "Refresh prices"}
      </button>
      {status.kind === "done" ? (
        <span className="text-sm text-ink-muted">
          Priced {status.priced}/{status.priced + status.unpriced}
          {status.unpriced > 0 ? " · some holdings couldn't be priced" : ""}
          {status.live ? "" : " · FX placeholder"}
        </span>
      ) : null}
      {status.kind === "error" ? (
        <span className="text-sm text-negative" role="alert">
          {status.message}
        </span>
      ) : null}
    </div>
  );
}
