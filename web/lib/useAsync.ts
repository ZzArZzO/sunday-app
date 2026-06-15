"use client";

import { useEffect, useState } from "react";

type AsyncState<T> = { data: T | null; loading: boolean; error: string | null };

/**
 * Fetch data on mount (client-side). Used by pages that became client components
 * for the static/Capacitor build — they fetch the FastAPI backend directly
 * (auth via cookie on web / Bearer token on mobile, handled in lib/api).
 *
 * One-shot on mount, mirroring the old server-component "fetch once per load".
 */
export function useAsync<T>(fn: () => Promise<T>): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ data: null, loading: true, error: null });

  useEffect(() => {
    let active = true;
    setState({ data: null, loading: true, error: null });
    fn()
      .then((data) => {
        if (active) setState({ data, loading: false, error: null });
      })
      .catch((err) => {
        if (active) {
          setState({ data: null, loading: false, error: err instanceof Error ? err.message : String(err) });
        }
      });
    return () => {
      active = false;
    };
    // Run once on mount — the fetch closure is intentionally not a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return state;
}
