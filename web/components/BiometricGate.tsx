"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Capacitor } from "@capacitor/core";

import { clearAuthToken, setAuthToken } from "@/lib/authToken";
import { isLockEnabled } from "@/lib/biometricPref";
import { clearPersistedToken, hasStoredSession, loadToken } from "@/lib/secureToken";

/**
 * Biometric app-lock. No-op on web (the session is an httpOnly cookie). On native
 * the token lives in the Keychain/Keystore and the OS won't release it without
 * Face ID / fingerprint, so reading it back IS the unlock. Children mount only
 * once unlocked, so nothing fetches with no auth behind the lock. The app re-locks
 * when it returns from the background.
 */
type Phase = "pending" | "locked" | "open";

function initialPhase(): Phase {
  // Web and SSR/prerender never gate; only a native runtime starts pending.
  if (typeof window === "undefined") return "open";
  return Capacitor.isNativePlatform() ? "pending" : "open";
}

export function BiometricGate({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<Phase>(initialPhase);
  const [failed, setFailed] = useState(false);
  const phaseRef = useRef<Phase>("pending");
  const verifyingRef = useRef(false);

  const setPhaseState = useCallback((next: Phase) => {
    phaseRef.current = next;
    setPhase(next);
  }, []);

  const unlock = useCallback(async () => {
    if (verifyingRef.current) return;
    verifyingRef.current = true;
    setFailed(false);
    try {
      const token = await loadToken(); // OS biometric prompt happens here
      if (token) {
        setAuthToken(token);
        setPhaseState("open");
      } else {
        setFailed(true);
      }
    } finally {
      verifyingRef.current = false;
    }
  }, [setPhaseState]);

  const signOut = useCallback(async () => {
    clearAuthToken();
    await clearPersistedToken();
    window.location.reload(); // back to the signed-out shell (routes to sign-in)
  }, []);

  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;
    let cancelled = false;

    // Register the resume listener first so an immediate background isn't missed.
    let remove: (() => void) | undefined;
    void (async () => {
      const { App } = await import("@capacitor/app");
      const handle = await App.addListener("appStateChange", ({ isActive }) => {
        if (!isActive) {
          if (isLockEnabled() && hasStoredSession()) {
            clearAuthToken(); // drop the in-memory token; re-lock on return
            setPhaseState("locked");
          }
        } else if (phaseRef.current === "locked") {
          void unlock();
        }
      });
      remove = () => void handle.remove();
    })();

    async function init() {
      if (!hasStoredSession()) {
        setPhaseState("open"); // not signed in — show the app (it routes to sign-in)
        return;
      }
      if (!isLockEnabled()) {
        const token = await loadToken(); // stored without biometric ACL — no prompt
        if (token) setAuthToken(token);
        if (!cancelled) setPhaseState("open");
        return;
      }
      if (!cancelled) {
        setPhaseState("locked");
        void unlock(); // surface the OS prompt immediately
      }
    }
    void init();

    return () => {
      cancelled = true;
      if (remove) remove();
    };
  }, [setPhaseState, unlock]);

  if (phase === "open") return <>{children}</>;
  if (phase === "pending") return null; // brief native init — avoids an unauth flash

  return (
    <div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 bg-surface px-8 text-center"
      role="dialog"
      aria-modal="true"
      aria-label="Sunday is locked"
    >
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-2 text-3xl">
        <span aria-hidden>🔒</span>
      </div>
      <div className="space-y-1">
        <p className="text-lg font-semibold text-ink">Sunday is locked</p>
        <p className="text-sm text-ink-muted">Unlock to view your portfolio.</p>
      </div>
      <button type="button" onClick={unlock} className="btn btn-primary">
        Unlock
      </button>
      {failed ? (
        <p className="text-sm text-negative" role="alert">
          Authentication failed. Tap Unlock to try again.
        </p>
      ) : null}
      <button type="button" onClick={signOut} className="text-sm text-ink-muted underline">
        Sign in with a different account
      </button>
    </div>
  );
}
