"use client";

import { useState } from "react";

import { requestMagicLink } from "@/lib/auth";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "sent"; email: string; devLink: string | null }
  | { kind: "error"; message: string };

export interface MagicLinkFormProps {
  /** Button label while idle, e.g. "Send sign-in link" or "Create account". */
  submitLabel: string;
  /** Heading shown on the "check your inbox" success card. */
  sentHeading: string;
}

/**
 * The actual magic-link request form, shared by /signin and /signup. The
 * backend treats new and returning users identically (one email in, one link
 * out) — the two pages exist purely to frame the same mechanism differently
 * for first-time vs. returning visitors, not because the flow itself differs.
 */
export function MagicLinkForm({ submitLabel, sentHeading }: MagicLinkFormProps) {
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

  if (state.kind === "sent") {
    return (
      <div className="card space-y-3 p-6">
        <p className="font-medium text-ink">{sentHeading}</p>
        <p className="text-sm leading-relaxed text-ink-muted">
          We sent a link to <strong>{state.email}</strong>. It expires in 15 minutes.
        </p>
        {state.devLink && /^https?:\/\//.test(state.devLink) ? (
          <p className="text-sm text-ink-muted">
            Dev mode (no email provider configured) —{" "}
            <a href={state.devLink} className="font-medium text-accent underline">
              open the link
            </a>
            .
          </p>
        ) : null}
      </div>
    );
  }

  return (
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
        {state.kind === "loading" ? "Sending…" : submitLabel}
      </button>
      {state.kind === "error" ? (
        <p className="text-sm text-negative" role="alert">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
