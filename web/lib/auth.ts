// Auth client — talks to the API's magic-link endpoints. Web uses the httpOnly
// session cookie; mobile (Capacitor) uses a stored Bearer token (lib/authToken).

import { clearAuthToken, getAuthToken, setAuthToken } from "@/lib/authToken";
import { isLockEnabled } from "@/lib/biometricPref";
import { clearPersistedToken, persistToken } from "@/lib/secureToken";

function apiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export type Me = {
  authenticated: boolean;
  email: string | null;
  country: string | null;
};

export type MagicLinkResult = {
  sent: boolean;
  dry_run: boolean;
  dev_link: string | null;
};

export async function requestMagicLink(email: string): Promise<MagicLinkResult> {
  const res = await fetch(`${apiUrl()}/api/auth/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    throw new Error(`${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<MagicLinkResult>;
}

export async function fetchMe(): Promise<Me> {
  try {
    const token = getAuthToken();
    const res = await fetch(`${apiUrl()}/api/auth/me`, {
      credentials: "include",
      cache: "no-store",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!res.ok) return { authenticated: false, email: null, country: null };
    return (await res.json()) as Me;
  } catch {
    return { authenticated: false, email: null, country: null };
  }
}

export async function logout(): Promise<void> {
  const token = getAuthToken();
  await fetch(`${apiUrl()}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  clearAuthToken();
  await clearPersistedToken();
}

/**
 * Mobile sign-in completion: trade a magic-link token for a session token and
 * store it (Bearer auth). Web doesn't use this — it gets a cookie via the
 * /api/auth/verify redirect.
 */
export async function exchangeMagicToken(magicToken: string): Promise<Me> {
  const res = await fetch(`${apiUrl()}/api/auth/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ magic_token: magicToken }),
  });
  if (!res.ok) {
    throw new Error(`${res.status}: ${await res.text()}`);
  }
  const data = (await res.json()) as {
    session_token: string;
    email: string | null;
    country: string | null;
  };
  setAuthToken(data.session_token);
  // Persist to the Keychain/Keystore, biometric-protected unless the user opted out.
  await persistToken(data.session_token, isLockEnabled());
  return { authenticated: true, email: data.email, country: data.country };
}
