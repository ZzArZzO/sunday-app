import { NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

/**
 * Behind Caddy's reverse proxy, `new URL(request.url).origin` reflects this
 * standalone server's own listen address (HOSTNAME=0.0.0.0, PORT=3000), not
 * the public domain the user actually connected to -- reconstruct the real
 * origin from the forwarded headers Caddy sets on every proxied request,
 * falling back to the request URL's own origin for local dev (no proxy).
 */
function publicOrigin(request: Request, requestUrl: URL): string {
  const forwardedHost = request.headers.get("x-forwarded-host");
  if (!forwardedHost) return requestUrl.origin;
  const forwardedProto = request.headers.get("x-forwarded-proto") ?? "https";
  return `${forwardedProto}://${forwardedHost}`;
}

/** Completes an OAuth (Google/Apple) sign-in redirect by exchanging the code for a session. */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const origin = publicOrigin(request, url);
  const code = url.searchParams.get("code");
  const next = url.searchParams.get("next") ?? "/";

  if (code) {
    const supabase = createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/signin?error=auth_callback_failed`);
}
