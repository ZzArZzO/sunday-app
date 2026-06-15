"use client";

import { useEffect, useState } from "react";
import { Capacitor } from "@capacitor/core";

import { registerForPush } from "@/lib/push";

type Status = "idle" | "working" | "on" | "denied" | "error";

/**
 * Double-opt-in priming for native push: we explain the value and ask in-app
 * *before* triggering the OS permission prompt, so a tentative tap doesn't burn
 * the one-shot system dialog. Renders nothing on web (push is app-only) and once
 * notifications are on.
 */
export function PushPrimer() {
  const [isNative, setIsNative] = useState(false);
  const [status, setStatus] = useState<Status>("idle");

  // isNativePlatform() is only meaningful client-side; gate render on it so the
  // static export / web preview shows nothing.
  useEffect(() => {
    setIsNative(Capacitor.isNativePlatform());
  }, []);

  if (!isNative || status === "on") return null;

  async function enable() {
    setStatus("working");
    try {
      const res = await registerForPush();
      if (!res.supported) setStatus("error");
      else setStatus(res.granted ? "on" : "denied");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="card p-5">
      <p className="font-medium text-ink">Get your briefing as a notification</p>
      <p className="mt-1 text-sm text-ink-muted">
        We&apos;ll send a single push every Sunday when your weekly briefing is ready. No other
        alerts.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={enable}
          disabled={status === "working"}
          className="btn btn-primary"
        >
          {status === "working" ? "Enabling…" : "Turn on notifications"}
        </button>
        {status === "denied" ? (
          <span className="text-sm text-ink-muted">
            Notifications are off in system settings — enable them there to receive your briefing.
          </span>
        ) : null}
        {status === "error" ? (
          <span className="text-sm text-negative" role="alert">
            Couldn&apos;t turn on notifications. Try again.
          </span>
        ) : null}
      </div>
    </div>
  );
}
