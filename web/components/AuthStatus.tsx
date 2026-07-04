"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchMe, signOut as supabaseSignOut, type Me } from "@/lib/auth";
import { createClient } from "@/lib/supabase/client";

/** Compact nav indicator: "Sign in" when logged out, email + "Sign out" when in. */
export function AuthStatus() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    let active = true;
    fetchMe().then((res) => {
      if (active) setMe(res);
    });

    const supabase = createClient();
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(() => {
      fetchMe().then((res) => {
        if (active) setMe(res);
      });
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  if (me === null) return null; // initial load — render nothing to avoid flicker

  if (!me.authenticated) {
    return (
      <Link
        href="/signin"
        className="rounded-md px-2.5 py-1.5 text-sm font-medium text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
      >
        Sign in
      </Link>
    );
  }

  async function signOut() {
    await supabaseSignOut();
    setMe({ authenticated: false, email: null, country: null });
    router.refresh();
  }

  return (
    <div className="flex items-center gap-2">
      <Link
        href="/account"
        className="hidden max-w-[140px] truncate text-xs text-ink-subtle hover:text-ink sm:inline"
        title={me.email ?? undefined}
      >
        {me.email}
      </Link>
      <button
        type="button"
        onClick={signOut}
        className="rounded-md px-2.5 py-1.5 text-sm font-medium text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
      >
        Sign out
      </button>
    </div>
  );
}
