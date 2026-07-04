"use client";

import { useState } from "react";

import { signInWithOAuth } from "@/lib/auth";

export function OAuthButtons() {
  const [pending, setPending] = useState<"google" | "apple" | null>(null);
  const [error, setError] = useState("");

  async function go(provider: "google" | "apple") {
    setError("");
    setPending(provider);
    try {
      await signInWithOAuth(provider);
      // On success the browser navigates away to the provider — nothing more to do here.
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setPending(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => go("google")}
          disabled={pending !== null}
          className="btn btn-ghost justify-center border border-rule"
        >
          {pending === "google" ? "Redirecting…" : "Google"}
        </button>
        <button
          type="button"
          onClick={() => go("apple")}
          disabled={pending !== null}
          className="btn btn-ghost justify-center border border-rule"
        >
          {pending === "apple" ? "Redirecting…" : "Apple"}
        </button>
      </div>
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
