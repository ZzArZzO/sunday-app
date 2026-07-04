"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { OAuthButtons } from "@/components/OAuthButtons";
import { signUpWithPassword } from "@/lib/auth";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "confirm_email" }
  | { kind: "error"; message: string };

const MIN_PASSWORD_LENGTH = 8;

export default function SignUpPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (state.kind === "loading") return;
    if (password.length < MIN_PASSWORD_LENGTH) {
      setState({ kind: "error", message: `Password must be at least ${MIN_PASSWORD_LENGTH} characters.` });
      return;
    }
    if (password !== confirmPassword) {
      setState({ kind: "error", message: "Passwords don't match." });
      return;
    }

    setState({ kind: "loading" });
    try {
      const { needsEmailConfirmation } = await signUpWithPassword(email.trim(), password);
      if (needsEmailConfirmation) {
        setState({ kind: "confirm_email" });
      } else {
        router.push("/dashboard");
        router.refresh();
      }
    } catch (err) {
      setState({ kind: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  return (
    <div className="container-prose mx-auto max-w-md space-y-8 py-10">
      <header className="space-y-2">
        <p className="label">Sign up</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink">
          Create your account
        </h1>
        <p className="text-base leading-relaxed text-ink-muted">
          Import a portfolio and see your first briefing in minutes. You can add an authenticator
          app for extra security afterward.
        </p>
      </header>

      {state.kind === "confirm_email" ? (
        <div className="card space-y-3 p-6">
          <p className="font-medium text-ink">Confirm your email</p>
          <p className="text-sm leading-relaxed text-ink-muted">
            We sent a confirmation link to <strong>{email.trim()}</strong>. Click it to activate
            your account, then come back here to log in.
          </p>
        </div>
      ) : (
        <>
          <OAuthButtons />
          <form onSubmit={submit} className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
              className="w-full rounded-md border border-rule bg-surface px-3 py-2.5 text-sm text-ink outline-none placeholder:text-ink-subtle focus:border-accent/50"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password (min. 8 characters)"
              autoComplete="new-password"
              required
              className="w-full rounded-md border border-rule bg-surface px-3 py-2.5 text-sm text-ink outline-none placeholder:text-ink-subtle focus:border-accent/50"
            />
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              autoComplete="new-password"
              required
              className="w-full rounded-md border border-rule bg-surface px-3 py-2.5 text-sm text-ink outline-none placeholder:text-ink-subtle focus:border-accent/50"
            />
            <button
              type="submit"
              className="btn btn-primary w-full justify-center"
              disabled={state.kind === "loading" || !email.trim() || !password || !confirmPassword}
            >
              {state.kind === "loading" ? "Creating account…" : "Create account"}
            </button>
            {state.kind === "error" ? (
              <p className="text-sm text-negative" role="alert">
                {state.message}
              </p>
            ) : null}
          </form>
        </>
      )}

      <p className="text-sm text-ink-muted">
        Already have an account?{" "}
        <Link href="/signin" className="font-medium text-accent hover:underline">
          Log in
        </Link>
      </p>

      <p className="text-xs leading-relaxed text-ink-subtle">
        Information and education only — Sunday is not a financial adviser. No broker login; your
        data stays yours.
      </p>
    </div>
  );
}
