// Bearer-token store for mobile (Capacitor) auth.
//
// The web build authenticates with httpOnly cookies and NEVER sets a token here,
// so `getAuthToken()` returns null on web and the cookie path is used. The mobile
// sign-in flow (`exchangeMagicToken`) stores the session token; requests then send
// it as `Authorization: Bearer …`.
//
// Backing store is `localStorage` for now; Build 3 swaps it for Capacitor
// Keychain/Keystore secure storage (and the token never lands in localStorage on
// web because web never calls `setAuthToken`).

const KEY = "sunday_session_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null; // SSR: cookie path handles auth
  try {
    return window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  try {
    window.localStorage.setItem(KEY, token);
  } catch {
    // storage unavailable — token simply won't persist
  }
}

export function clearAuthToken(): void {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    // no-op
  }
}
