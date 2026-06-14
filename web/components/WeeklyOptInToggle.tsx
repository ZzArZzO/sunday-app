"use client";

import { useEffect, useState } from "react";

import { fetchDeliveryPreferences, updateDeliveryPreferences } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ready"; optIn: boolean; saving: boolean }
  | { kind: "error"; message: string };

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

/**
 * Opt in/out of the Sunday weekly briefing email. The weekly cron only sends to
 * users who turn this on — off by default, no unsolicited briefings.
 */
export function WeeklyOptInToggle() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    fetchDeliveryPreferences()
      .then((prefs) => {
        if (active) setState({ kind: "ready", optIn: prefs.weekly_opt_in, saving: false });
      })
      .catch((err) => {
        if (active) setState({ kind: "error", message: errorMessage(err) });
      });
    return () => {
      active = false;
    };
  }, []);

  async function toggle(next: boolean) {
    setState({ kind: "ready", optIn: next, saving: true });
    try {
      const prefs = await updateDeliveryPreferences(next);
      setState({ kind: "ready", optIn: prefs.weekly_opt_in, saving: false });
    } catch (err) {
      setState({ kind: "error", message: errorMessage(err) });
    }
  }

  if (state.kind === "loading") {
    return <p className="text-sm text-ink-muted">Loading email preference…</p>;
  }
  if (state.kind === "error") {
    return (
      <p className="text-sm text-negative" role="alert">
        Couldn&apos;t load email preference: {state.message}
      </p>
    );
  }

  return (
    <label className="flex cursor-pointer items-center gap-3">
      <input
        type="checkbox"
        checked={state.optIn}
        disabled={state.saving}
        onChange={(e) => toggle(e.target.checked)}
        className="h-4 w-4 accent-[var(--positive)]"
      />
      <span className="text-sm text-ink">
        Email me this briefing every Sunday
        {state.saving ? <span className="text-ink-muted"> · saving…</span> : null}
      </span>
    </label>
  );
}
