"use client";

import { useEffect, useState } from "react";
import { Capacitor } from "@capacitor/core";

import { getAuthToken } from "@/lib/authToken";
import { isBiometricAvailable } from "@/lib/biometric";
import { isLockEnabled, setLockEnabled } from "@/lib/biometricPref";
import { persistToken } from "@/lib/secureToken";

/**
 * Settings toggle for the biometric app-lock. Renders only on a native device
 * that actually has biometrics enrolled; hidden on web.
 */
export function BiometricLockToggle() {
  const [available, setAvailable] = useState(false);
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;
    void isBiometricAvailable().then((ok) => {
      setAvailable(ok);
      if (ok) setEnabled(isLockEnabled());
    });
  }, []);

  if (!available) return null;

  function toggle() {
    const next = !enabled;
    setEnabled(next);
    setLockEnabled(next);
    // Re-store the token with/without the OS biometric ACL so the change applies
    // on the next launch, not just to the verify gesture.
    const token = getAuthToken();
    if (token) void persistToken(token, next);
  }

  return (
    <div className="card flex items-center justify-between gap-4 p-5">
      <div>
        <p className="font-medium text-ink">Require biometric unlock</p>
        <p className="mt-1 text-sm text-ink-muted">
          Lock Sunday with Face ID / fingerprint when you open or return to it.
        </p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        aria-label="Require biometric unlock"
        onClick={toggle}
        className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
          enabled ? "bg-accent" : "bg-surface-2"
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-surface shadow-soft transition-transform ${
            enabled ? "translate-x-5" : "translate-x-0.5"
          }`}
        />
      </button>
    </div>
  );
}
