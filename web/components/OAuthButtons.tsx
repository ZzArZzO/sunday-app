"use client";

import { useState } from "react";

import { signInWithOAuth } from "@/lib/auth";

export function OAuthButtons() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function goGoogle() {
    setError("");
    setPending(true);
    try {
      await signInWithOAuth("google");
      // On success the browser navigates away to the provider — nothing more to do here.
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setPending(false);
    }
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={goGoogle}
        disabled={pending}
        className="btn btn-ghost w-full justify-center border border-rule"
      >
        {pending ? "Redirecting…" : "Continue with Google"}
      </button>
      {error ? (
        <p className="text-sm text-negative" role="alert">
          {error}
        </p>
      ) : null}
      <div className="flex items-center gap-3 text-xs text-ink-subtle">
        <span className="h-px flex-1 bg-rule" />
        or
        <span className="h-px flex-1 bg-rule" />
      </div>
    </div>
  );
}
