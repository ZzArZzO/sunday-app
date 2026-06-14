"use client";

import { useEffect, useState } from "react";

import { fetchEvents } from "@/lib/api";
import type { EventsResponse, NewsItemView } from "@/lib/types";

// "What changed this week" — the real holdings-tagged news + upcoming earnings
// behind the briefing's prose. Purely descriptive (headlines + summaries),
// never directive. Self-fetches because /api/events does a (daily-cached)
// network call that can be slow or unavailable.

function shortDate(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString("en-IE", { day: "numeric", month: "short" });
}

export function EventsCard() {
  const [data, setData] = useState<EventsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchEvents()
      .then((res) => {
        if (active) setData(res);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const isEmpty = data && data.news.length === 0 && data.earnings.length === 0;

  return (
    <section className="space-y-4">
      <p className="label">What changed this week</p>
      <div className="card p-5">
        {loading ? (
          <div className="space-y-3">
            <div className="skeleton h-4 w-1/3" />
            <div className="skeleton h-4 w-2/3" />
            <div className="skeleton h-4 w-1/2" />
          </div>
        ) : error ? (
          <p className="text-sm text-ink-muted">
            Live news for your holdings is unavailable right now.
          </p>
        ) : isEmpty ? (
          <p className="text-sm text-ink-muted">
            No notable news or upcoming earnings for your holdings in the last week.
          </p>
        ) : data ? (
          <div className="space-y-5">
            {data.earnings.length > 0 ? (
              <div className="space-y-2">
                <p className="label">Upcoming earnings</p>
                <ul className="flex flex-wrap gap-2">
                  {data.earnings.map((e) => (
                    <li
                      key={`${e.ticker}-${e.date}`}
                      className="inline-flex items-center gap-2 rounded-md border border-rule bg-surface-2/60 px-2.5 py-1 text-sm"
                    >
                      <span className="font-semibold text-ink">{e.ticker}</span>
                      <span className="font-mono text-xs text-ink-muted">{shortDate(e.date)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {data.news.length > 0 ? (
              <div className="space-y-3">
                <p className="label">In the news</p>
                <ul className="divide-y divide-rule">
                  {data.news.map((n, i) => (
                    <NewsRow key={`${n.holding}-${i}`} item={n} />
                  ))}
                </ul>
              </div>
            ) : null}

            <p className="text-xs text-ink-subtle">
              Headlines for the names you hold — information only, not advice.
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function NewsRow({ item }: { item: NewsItemView }) {
  const date = shortDate(item.published_at);
  const meta = [item.publisher, date].filter(Boolean).join(" · ");
  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <div className="flex items-baseline gap-2">
        <span className="inline-flex flex-none items-center rounded-md border border-rule bg-surface-2 px-1.5 py-0.5 text-xs font-medium text-ink-muted">
          {item.holding}
        </span>
        {item.url ? (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-ink hover:text-accent hover:underline"
          >
            {item.title}
          </a>
        ) : (
          <span className="text-sm font-medium text-ink">{item.title}</span>
        )}
      </div>
      {item.summary ? (
        <p className="mt-1 line-clamp-2 text-sm text-ink-muted">{item.summary}</p>
      ) : null}
      {meta ? <p className="mt-1 text-xs text-ink-subtle">{meta}</p> : null}
    </li>
  );
}
