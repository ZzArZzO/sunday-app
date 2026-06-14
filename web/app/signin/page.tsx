"use client";

import { useState } from "react";

import { requestMagicLink } from "@/lib/auth";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "sent"; email: string; devLink: string | null }
  | { kind: "error"; message: string };

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const value = email.trim();
    if (!value || state.kind === "loading") return;
    setState({ kind: "loading" });
    try {
      const res = await requestMagicLink(value);
      setState({ kind: "sent", email: value, devLink: res.dev_link });
    } catch (err) {
      setState({ kind: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  return (
    <div className="container-prose mx-auto max-w-md space-y-8 py-10">
      <header className="space-y-2">
        <p className="label">Sign in</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink">
          Your Sunday, your account
        </h1>
        <p className="text-base leading-relaxed text-ink-muted">
          Enter your email and we&apos;ll send you a one-tap sign-in link. No password.
        </p>
      </header>

      {state.kind === "sent" ? (
        <div className="card space-y-3 p-6">
          <p className="font-medium text-ink">Check your inbox</p>
          <p className="text-sm leading-relaxed text-ink-muted">
            We sent a sign-in link to <strong>{state.email}</strong>. It expires in 15 minutes.
          </p>
          {state.devLink ? (
            <p className="text-sm text-ink-muted">
              Dev mode (no email provider configured) —{" "}
              <a href={state.devLink} className="font-medium text-accent underline">
                open the sign-in link
              </a>
              .
            </p>
          ) : null}
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            className="w-full rounded-md border border-rule bg-surface px-3 py-2.5 text-sm text-ink outline-none placeholder:text-ink-subtle focus:border-accent/50"
          />
          <button
            type="submit"
            className="btn btn-primary w-full justify-center"
            disabled={state.kind === "loading" || !email.trim()}
          >
            {state.kind === "loading" ? "Sending…" : "Send sign-in link"}
          </button>
          {state.kind === "error" ? (
            <p className="text-sm text-negative" role="alert">
              {state.message}
            </p>
          ) : null}
        </form>
      )}

      <p className="text-xs leading-relaxed text-ink-subtle">
        Information and education only — Sunday is not a financial adviser. No broker login; your
        data stays yours.
      </p>
    </div>
  );
}
