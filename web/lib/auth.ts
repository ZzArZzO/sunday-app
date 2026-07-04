// Auth client — Supabase Auth (email/password, TOTP MFA, Google/Apple OAuth).
// The Supabase browser client manages its own session cookie; api.ts reads it
// via getSession() and forwards the access token as a Bearer header.

import { createClient } from "@/lib/supabase/client";

export type Me = {
  authenticated: boolean;
  email: string | null;
  country: string | null;
};

export async function signUpWithPassword(
  email: string,
  password: string,
): Promise<{ needsEmailConfirmation: boolean }> {
  const { data, error } = await createClient().auth.signUp({ email, password });
  if (error) throw new Error(error.message);
  // Supabase issues a session immediately unless "Confirm email" is on for the project.
  return { needsEmailConfirmation: !data.session };
}

export async function signInWithPassword(email: string, password: string): Promise<void> {
  const { error } = await createClient().auth.signInWithPassword({ email, password });
  if (error) throw new Error(error.message);
}

export async function signInWithOAuth(provider: "google" | "apple"): Promise<void> {
  const { error } = await createClient().auth.signInWithOAuth({
    provider,
    options: { redirectTo: `${window.location.origin}/auth/callback` },
  });
  if (error) throw new Error(error.message);
}

export async function signOut(): Promise<void> {
  await createClient().auth.signOut();
}

export async function fetchMe(): Promise<Me> {
  const {
    data: { session },
  } = await createClient().auth.getSession();
  if (!session) return { authenticated: false, email: null, country: null };

  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await fetch(`${apiUrl}/api/auth/me`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${session.access_token}` },
    });
    if (!res.ok) return { authenticated: false, email: null, country: null };
    return (await res.json()) as Me;
  } catch {
    return { authenticated: false, email: null, country: null };
  }
}
