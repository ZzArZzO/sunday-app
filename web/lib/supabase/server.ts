import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

/** Server Component / Route Handler Supabase client — reads/writes the session cookie. */
export function createClient() {
  const cookieStore = cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // Called from a Server Component with no response to attach
            // cookies to — fine as long as middleware.ts refreshes sessions.
          }
        },
      },
    },
  );
}
