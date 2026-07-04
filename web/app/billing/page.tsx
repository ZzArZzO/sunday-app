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

// Reflects the app's actual gates (SourcesManager's live-sync ProGate,
// WeeklyOptInToggle's automatic delivery) — not a marketing wishlist.
const FREE_FEATURES = [
  "Full dashboard and weekly briefing, always",
  "Import any broker via CSV — Trade Republic, Scalable, DEGIRO, and more",
  "AI assistant grounded in your portfolio",
  "Download the briefing as a PDF, or send it to yourself on demand",
];

const PRO_ONLY_FEATURES = [
  "Automatic weekly briefing delivered by email, every Sunday",
  "Live wallet sync — Ethereum, its L2s, and Solana",
  "Live exchange sync — Bitvavo, Kraken, Coinbase, Binance",
];

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
        <div className="space-y-6">
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

          {load.sub.is_pro ? (
            <div className="card space-y-3 p-5">
              <p className="label">Included with Pro</p>
              <ul className="space-y-2">
                {[...FREE_FEATURES, ...PRO_ONLY_FEATURES].map((f) => (
                  <FeatureRow key={f} included label={f} />
                ))}
              </ul>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="card space-y-3 p-5">
                <p className="label">Free</p>
                <p className="font-mono text-2xl font-semibold tabular-nums text-ink">€0</p>
                <ul className="space-y-2 pt-1">
                  {FREE_FEATURES.map((f) => (
                    <FeatureRow key={f} included label={f} />
                  ))}
                  {PRO_ONLY_FEATURES.map((f) => (
                    <FeatureRow key={f} included={false} label={f} />
                  ))}
                </ul>
              </div>
              <div className="card space-y-3 border-accent/40 bg-accent-subtle/20 p-5">
                <p className="label text-accent">Pro</p>
                <p className="font-mono text-2xl font-semibold tabular-nums text-ink">€9/mo</p>
                <ul className="space-y-2 pt-1">
                  {[...FREE_FEATURES, ...PRO_ONLY_FEATURES].map((f) => (
                    <FeatureRow key={f} included label={f} />
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      ) : null}

      <Disclaimer />
    </div>
  );
}

function FeatureRow({ included, label }: { included: boolean; label: string }) {
  return (
    <li className={`flex items-start gap-2 text-sm ${included ? "text-ink" : "text-ink-subtle"}`}>
      <span
        aria-hidden
        className={`mt-0.5 inline-flex h-4 w-4 flex-none items-center justify-center rounded-full text-[10px] ${
          included ? "bg-positive-subtle text-positive" : "bg-surface-2 text-ink-subtle"
        }`}
      >
        {included ? "✓" : "–"}
      </span>
      <span>{label}</span>
    </li>
  );
}
