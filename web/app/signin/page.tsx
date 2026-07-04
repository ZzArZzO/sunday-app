"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { OAuthButtons } from "@/components/OAuthButtons";
import { signInWithPassword } from "@/lib/auth";
import { needsMfaChallenge, verifyTotpChallenge } from "@/lib/mfa";

type Phase = "password" | "mfa";
type Status = { kind: "idle" } | { kind: "loading" } | { kind: "error"; message: string };

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [phase, setPhase] = useState<Phase>("password");
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (status.kind === "loading") return;
    setStatus({ kind: "loading" });
    try {
      await signInWithPassword(email.trim(), password);
      if (await needsMfaChallenge()) {
        setPhase("mfa");
        setStatus({ kind: "idle" });
      } else {
        router.push("/dashboard");
        router.refresh();
      }
    } catch (err) {
      setStatus({ kind: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  async function submitMfa(e: React.FormEvent) {
    e.preventDefault();
    setStatus({ kind: "loading" });
    try {
      await verifyTotpChallenge(mfaCode.trim());
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setStatus({ kind: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }

  if (phase === "mfa") {
    return (
      <div className="container-prose mx-auto max-w-md space-y-8 py-10">
        <header className="space-y-2">
          <p className="label">Two-factor authentication</p>
          <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink">
            Enter your code
          </h1>
          <p className="text-base leading-relaxed text-ink-muted">
            Open your authenticator app and enter the 6-digit code for Sunday.
          </p>
        </header>
        <form onSubmit={submitMfa} className="space-y-4">
          <input
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            value={mfaCode}
            onChange={(e) => setMfaCode(e.target.value.trim())}
            placeholder="123456"
            autoFocus
            className="w-full rounded-md border border-rule bg-surface px-3 py-2.5 text-center text-lg tracking-[0.3em] text-ink outline-none focus:border-accent/50"
          />
          <button
            type="submit"
            className="btn btn-primary w-full justify-center"
            disabled={status.kind === "loading" || mfaCode.length < 6}
          >
            {status.kind === "loading" ? "Verifying…" : "Verify"}
          </button>
          {status.kind === "error" ? (
            <p className="text-sm text-negative" role="alert">
              {status.message}
            </p>
          ) : null}
        </form>
      </div>
    );
  }

  return (
    <div className="container-prose mx-auto max-w-md space-y-8 py-10">
      <header className="space-y-2">
        <p className="label">Log in</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink">Welcome back</h1>
        <p className="text-base leading-relaxed text-ink-muted">Enter your email and password.</p>
      </header>

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
          placeholder="Password"
          autoComplete="current-password"
          required
          className="w-full rounded-md border border-rule bg-surface px-3 py-2.5 text-sm text-ink outline-none placeholder:text-ink-subtle focus:border-accent/50"
        />
        <button
          type="submit"
          className="btn btn-primary w-full justify-center"
          disabled={status.kind === "loading" || !email.trim() || !password}
        >
          {status.kind === "loading" ? "Logging in…" : "Log in"}
        </button>
        {status.kind === "error" ? (
          <p className="text-sm text-negative" role="alert">
            {status.message}
          </p>
        ) : null}
      </form>

      <p className="text-sm text-ink-muted">
        New to Sunday?{" "}
        <Link href="/signup" className="font-medium text-accent hover:underline">
          Create an account
        </Link>
      </p>

      <p className="text-xs leading-relaxed text-ink-subtle">
        Information and education only — Sunday is not a financial adviser. No broker login; your
        data stays yours.
      </p>
    </div>
  );
}
