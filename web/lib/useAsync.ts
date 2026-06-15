"use client";

import { useCallback, useEffect, useState } from "react";

type AsyncState<T> = { data: T | null; loading: boolean; error: string | null };

/**
 * Fetch data on mount (client-side), with a `refetch()` to re-run on demand.
 * Used by pages that became client components for the static/Capacitor build —
 * they fetch the FastAPI backend directly (auth via cookie on web / Bearer on
 * mobile, handled in lib/api). Prior data is kept while refetching so callers
 * can show the existing view instead of a skeleton on refresh.
 */
export function useAsync<T>(fn: () => Promise<T>): AsyncState<T> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ data: null, loading: true, error: null });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => {
        if (active) setState({ data, loading: false, error: null });
      })
      .catch((err) => {
        if (active) {
          setState((s) => ({
            data: s.data,
            loading: false,
            error: err instanceof Error ? err.message : String(err),
          }));
        }
      });
    return () => {
      active = false;
    };
    // Re-runs when `tick` changes (refetch); the fetch closure is intentionally
    // not a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick]);

  const refetch = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, refetch };
}
