// Device-side secure persistence for the session token (native only), backed by
// the Keychain (iOS) / Keystore (Android) via the native-biometric plugin. On
// web this is a no-op: the browser keeps the httpOnly session cookie instead.
//
// This replaces the old localStorage token store (insecure, JS-readable). When
// stored `secure`, the credential is biometric-protected at the OS layer — the
// system itself refuses getCredentials without a successful Face ID / fingerprint,
// so the lock holds even if app code is bypassed. BIOMETRY_ANY (not CURRENT_SET)
// is used so adding a fingerprint later doesn't invalidate the stored token.

import { Capacitor } from "@capacitor/core";

const SERVER = "com.sunday.app";
const USERNAME = "session";
// A plain marker (not a secret) so the gate can tell "signed in but locked" from
// "not signed in" without triggering a biometric prompt just to check.
const SESSION_FLAG = "sunday_session_present";

function setSessionFlag(present: boolean): void {
  try {
    if (present) window.localStorage.setItem(SESSION_FLAG, "1");
    else window.localStorage.removeItem(SESSION_FLAG);
  } catch {
    // storage unavailable — the gate falls back to attempting a load
  }
}

/** True if a session token is stored on this device (i.e. signed in). */
export function hasStoredSession(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(SESSION_FLAG) === "1";
  } catch {
    return false;
  }
}

/** Persist the session token. When `secure`, the OS requires biometric auth to
 * read it back (and, on Android, to store it). No-op on web. */
export async function persistToken(token: string, secure: boolean): Promise<void> {
  if (!Capacitor.isNativePlatform()) {
    setSessionFlag(true);
    return;
  }
  const { NativeBiometric, AccessControl } = await import("@capgo/capacitor-native-biometric");
  try {
    await NativeBiometric.setCredentials({
      username: USERNAME,
      password: token,
      server: SERVER,
      accessControl: secure ? AccessControl.BIOMETRY_ANY : AccessControl.NONE,
    });
    setSessionFlag(true);
  } catch {
    // Store failed (e.g. the user cancelled the biometric enrol prompt). Leave the
    // marker unset — the in-memory token still works until the app restarts.
  }
}

/** Read the stored token. If it was stored `secure`, the OS shows a biometric
 * prompt here and rejects on cancel/failure. Returns null if absent or denied. */
export async function loadToken(): Promise<string | null> {
  if (!Capacitor.isNativePlatform()) return null;
  const { NativeBiometric } = await import("@capgo/capacitor-native-biometric");
  try {
    const creds = await NativeBiometric.getCredentials({ server: SERVER });
    return creds.password || null;
  } catch {
    return null; // absent, or biometric cancelled/failed
  }
}

export async function clearPersistedToken(): Promise<void> {
  setSessionFlag(false);
  if (!Capacitor.isNativePlatform()) return;
  const { NativeBiometric } = await import("@capgo/capacitor-native-biometric");
  try {
    await NativeBiometric.deleteCredentials({ server: SERVER });
  } catch {
    // already absent — nothing to do
  }
}
