// In-memory session-token store for Bearer auth (mobile / Capacitor).
//
// The web build authenticates with httpOnly cookies and never sets a token here,
// so getAuthToken() returns null on web and the cookie path is used. On mobile
// the token is held in memory for the session (read synchronously per request by
// lib/api) and persisted across launches in the device Keychain/Keystore via
// lib/secureToken — loaded back into memory only after biometric unlock
// (see components/BiometricGate).
//
// In-memory (not localStorage) is deliberate: nothing readable-at-rest by JS.

let memoryToken: string | null = null;

export function getAuthToken(): string | null {
  return memoryToken;
}

export function setAuthToken(token: string): void {
  memoryToken = token;
}

export function clearAuthToken(): void {
  memoryToken = null;
}
