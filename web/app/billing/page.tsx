"use client";

import { useEffect, useState } from "react";

import { Disclaimer } from "@/components/Disclaimer";
import { fetchSubscription, openBillingPortal, startCheckout } from "@/lib/api";
import type { Subscription } from "@/lib/types";

type Load =
  | { kind: "loading" }
  | { kind: "ready"; sub: Subscription }
  | { kind: "error"; message: string };

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

export default function BillingPage() {
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [banner, setBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("status");
    if (status === "success") setBanner("Thanks — your subscription is being activated.");
    if (status === "cancel") setBanner("Checkout cancelled. No charge was made.");

    fetchSubscription()
      .then((sub) => setLoad({ kind: "ready", sub }))
      .catch((err) => setLoad({ kind: "error", message: errorMessage(err) }));
  }, []);

  async function redirectVia(action: () => Promise<{ url: string }>) {
    setBusy(true);
    setActionError(null);
    try {
      const { url } = await action();
      window.location.href = url;
    } catch (err) {
      setActionError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <div className="container-prose space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Billing</h1>
        <p className="text-sm text-ink-muted">Manage your Sunday subscription.</p>
      </header>

      {banner ? (
        <div className="card bg-positive-subtle/40 p-4 text-sm text-ink">{banner}</div>
      ) : null}

      {load.kind === "loading" ? (
        <p className="text-sm text-ink-muted">Loading your plan…</p>
      ) : null}

      {load.kind === "error" ? (
        <div className="card border-negative/30 bg-negative-subtle/40 p-4">
          <p className="text-sm text-negative">Couldn&apos;t load your plan: {load.message}</p>
        </div>
      ) : null}

      {load.kind === "ready" ? (
        <div className="card space-y-4 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-ink-muted">Current plan</p>
              <p className="text-xl font-semibold capitalize">{load.sub.tier}</p>
            </div>
            {load.sub.is_pro ? (
              <span className="rounded-full bg-positive-subtle px-3 py-1 text-xs font-medium text-positive">
                Active
              </span>
            ) : null}
          </div>

          {load.sub.is_pro ? (
            <button
              type="button"
              onClick={() => redirectVia(openBillingPortal)}
              disabled={busy}
              className="btn btn-ghost"
            >
              {busy ? "Opening…" : "Manage subscription"}
            </button>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-ink">
                Upgrade to <strong>Pro</strong> — €9/mo. Cancel anytime.
              </p>
              <button
                type="button"
                onClick={() => redirectVia(startCheckout)}
                disabled={busy}
                className="btn btn-primary"
              >
                {busy ? "Redirecting…" : "Upgrade to Pro"}
              </button>
            </div>
          )}

          {actionError ? (
            <p className="text-sm text-negative" role="alert">
              {actionError}
            </p>
          ) : null}
        </div>
      ) : null}

      <Disclaimer />
    </div>
  );
}
