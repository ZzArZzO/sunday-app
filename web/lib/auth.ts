// Auth client — talks to the API's magic-link endpoints with the session cookie.
// Kept separate from lib/api.ts so it's easy to reason about credentialed calls.

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
    const res = await fetch(`${apiUrl()}/api/auth/me`, {
      credentials: "include",
      cache: "no-store",
    });
    if (!res.ok) return { authenticated: false, email: null, country: null };
    return (await res.json()) as Me;
  } catch {
    return { authenticated: false, email: null, country: null };
  }
}

export async function logout(): Promise<void> {
  await fetch(`${apiUrl()}/api/auth/logout`, { method: "POST", credentials: "include" });
}
