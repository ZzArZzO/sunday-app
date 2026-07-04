"use client";

import { useEffect, useState } from "react";

import { enrollTotp, listTotpFactors, unenrollTotp, verifyTotpEnrollment, type TotpFactor } from "@/lib/mfa";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

type Load = { kind: "loading" } | { kind: "ready"; factors: TotpFactor[] } | { kind: "error"; message: string };
type Enrollment = { kind: "idle" } | { kind: "in_progress"; factorId: string; qrCodeSvg: string; secret: string };

export default function AccountPage() {
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [enrollment, setEnrollment] = useState<Enrollment>({ kind: "idle" });
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  function refresh() {
    listTotpFactors()
      .then((factors) => setLoad({ kind: "ready", factors }))
      .catch((err) => setLoad({ kind: "error", message: errorMessage(err) }));
  }

  useEffect(refresh, []);

  async function startEnroll() {
    setActionError(null);
    setBusy(true);
    try {
      const result = await enrollTotp();
      setEnrollment({ kind: "in_progress", factorId: result.factorId, qrCodeSvg: result.qrCodeSvg, secret: result.secret });
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function confirmEnroll(e: React.FormEvent) {
    e.preventDefault();
    if (enrollment.kind !== "in_progress") return;
    setBusy(true);
    setActionError(null);
    try {
      await verifyTotpEnrollment(enrollment.factorId, code.trim());
      setEnrollment({ kind: "idle" });
      setCode("");
      refresh();
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove(factorId: string) {
    setBusy(true);
    setActionError(null);
    try {
      await unenrollTotp(factorId);
      refresh();
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container-prose mx-auto max-w-md space-y-10 py-10">
      <header className="space-y-2">
        <p className="label">Account</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Security
        </h1>
        <p className="text-base leading-relaxed text-ink-muted">
          Add an authenticator app for a second sign-in step, on top of your password.
        </p>
      </header>

      {actionError ? (
        <div role="alert" className="rounded-md border border-negative/30 bg-negative-subtle/40 p-3 text-sm text-negative">
          {actionError}
        </div>
      ) : null}

      {load.kind === "loading" ? <p className="text-sm text-ink-muted">Loading…</p> : null}
      {load.kind === "error" ? (
        <p className="text-sm text-negative">Couldn&apos;t load your security settings: {load.message}</p>
      ) : null}

      {load.kind === "ready" && enrollment.kind === "idle" ? (
        <section className="space-y-3">
          <p className="label">Authenticator app</p>
          {load.factors.length === 0 ? (
            <div className="card space-y-3 p-5">
              <p className="text-sm text-ink-muted">
                No authenticator app is set up yet. Adding one means signing in will need your
                password plus a 6-digit code from an app like Google Authenticator or Authy.
              </p>
              <button type="button" onClick={startEnroll} disabled={busy} className="btn btn-primary">
                {busy ? "Starting…" : "Set up authenticator app"}
              </button>
            </div>
          ) : (
            <ul className="space-y-2">
              {load.factors.map((f) => (
                <li key={f.id} className="card flex items-center justify-between gap-3 p-4">
                  <div>
                    <p className="font-medium text-ink">{f.friendlyName ?? "Authenticator app"}</p>
                    <p className="text-xs text-ink-subtle">{f.status === "verified" ? "Active" : "Pending verification"}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => remove(f.id)}
                    disabled={busy}
                    className="btn btn-ghost text-negative"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      {enrollment.kind === "in_progress" ? (
        <section className="card space-y-4 p-5">
          <p className="font-medium text-ink">Scan this QR code</p>
          <p className="text-sm text-ink-muted">
            Scan it with your authenticator app, or enter this key manually:{" "}
            <code className="rounded bg-surface-2 px-1.5 py-0.5 text-xs">{enrollment.secret}</code>
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element -- inline SVG data URI, not a Next-optimizable asset */}
          <img
            src={`data:image/svg+xml;utf8,${encodeURIComponent(enrollment.qrCodeSvg)}`}
            alt="Authenticator QR code"
            className="mx-auto h-48 w-48 rounded-md border border-rule bg-white p-2"
          />
          <form onSubmit={confirmEnroll} className="space-y-3">
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={(e) => setCode(e.target.value.trim())}
              placeholder="123456"
              className="w-full rounded-md border border-rule bg-surface px-3 py-2.5 text-center text-lg tracking-[0.3em] text-ink outline-none focus:border-accent/50"
            />
            <div className="flex gap-2">
              <button type="submit" disabled={busy || code.length < 6} className="btn btn-primary flex-1">
                {busy ? "Verifying…" : "Enable"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setEnrollment({ kind: "idle" });
                  setCode("");
                }}
                className="btn btn-ghost"
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </div>
  );
}
