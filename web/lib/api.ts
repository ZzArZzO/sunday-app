import type {
  BenchmarkResponse,
  BriefingResponse,
  ChatGrounding,
  ChatMessage,
  ChatResponse,
  DeliveryPreferences,
  DeliveryResult,
  DividendResponse,
  EventsResponse,
  FireResponse,
  IngestPreviewResponse,
  IngestResult,
  PortfolioResponse,
  PriceRefreshResponse,
  RebalanceResponse,
  Subscription,
  SupportedCountry,
  TaxSummaryResponse,
} from "@/lib/types";
import { getAuthToken } from "@/lib/authToken";

function getApiUrl(): string {
  if (typeof window === "undefined") {
    return process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...((init?.headers as Record<string, string> | undefined) ?? {}),
  };
  const fetchInit: RequestInit = { ...init, cache: "no-store", headers };

  if (typeof window === "undefined") {
    // Server component: forward the caller's session cookie to the API so the
    // request is scoped to the logged-in user (not the demo fallback).
    try {
      const { cookies } = await import("next/headers");
      const cookieHeader = cookies().toString();
      if (cookieHeader) headers["Cookie"] = cookieHeader;
    } catch {
      // Not inside a request scope (e.g. at build time) — skip.
    }
  } else {
    // Browser: include the cross-origin session cookie (web), and a stored
    // Bearer token if present (mobile / Capacitor — see lib/authToken).
    fetchInit.credentials = "include";
    const token = getAuthToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${getApiUrl()}${path}`, fetchInit);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status} ${path}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchPortfolio(): Promise<PortfolioResponse> {
  return http<PortfolioResponse>("/api/portfolio");
}

export async function fetchBriefing(): Promise<BriefingResponse> {
  return http<BriefingResponse>("/api/briefing");
}

/** Email the signed-in user this week's briefing now (dry-run without a Resend key). */
export async function sendMyBriefing(): Promise<DeliveryResult> {
  return http<DeliveryResult>("/api/delivery/briefing", { method: "POST" });
}

/** Read the signed-in user's weekly-email opt-in preference. */
export async function fetchDeliveryPreferences(): Promise<DeliveryPreferences> {
  return http<DeliveryPreferences>("/api/delivery/preferences");
}

/** Set the signed-in user's weekly-email opt-in preference. */
export async function updateDeliveryPreferences(
  weeklyOptIn: boolean,
): Promise<DeliveryPreferences> {
  return http<DeliveryPreferences>("/api/delivery/preferences", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ weekly_opt_in: weeklyOptIn }),
  });
}

/**
 * Fetch the one-page briefing PDF as a Blob. Browser-only — uses credentials so
 * the download is scoped to the signed-in user's portfolio (not the demo fallback).
 */
export async function fetchBriefingPdf(): Promise<Blob> {
  const headers: Record<string, string> = { Accept: "application/pdf" };
  const token = getAuthToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${getApiUrl()}/api/briefing/pdf`, {
    cache: "no-store",
    credentials: "include",
    headers,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status} /api/briefing/pdf: ${detail}`);
  }
  return res.blob();
}

export async function fetchFire(): Promise<FireResponse> {
  return http<FireResponse>("/api/fire");
}

/** Current subscription tier/status for the signed-in user. */
export async function fetchSubscription(): Promise<Subscription> {
  return http<Subscription>("/api/billing/subscription");
}

/** Start a Stripe Checkout Session for the Pro plan; returns a redirect URL. */
export async function startCheckout(): Promise<{ url: string }> {
  return http<{ url: string }>("/api/billing/checkout", { method: "POST" });
}

/** Open the Stripe Customer Portal to manage the subscription; returns a URL. */
export async function openBillingPortal(): Promise<{ url: string }> {
  return http<{ url: string }>("/api/billing/portal", { method: "POST" });
}

export async function fetchDividend(): Promise<DividendResponse> {
  return http<DividendResponse>("/api/dividend");
}

export async function fetchTax(): Promise<TaxSummaryResponse> {
  return http<TaxSummaryResponse>("/api/tax");
}

/** Countries the tax engine supports — drives the country selector. */
export async function fetchSupportedCountries(): Promise<SupportedCountry[]> {
  return http<SupportedCountry[]>("/api/tax/countries");
}

/** Set the signed-in user's tax-residence country (ISO-3166 alpha-2). */
export async function updateCountry(code: string): Promise<{ country: string | null }> {
  return http<{ country: string | null }>("/api/auth/country", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ country: code }),
  });
}

export async function fetchRebalance(): Promise<RebalanceResponse> {
  return http<RebalanceResponse>("/api/rebalance");
}

export async function fetchBenchmark(index: string): Promise<BenchmarkResponse> {
  return http<BenchmarkResponse>(`/api/benchmark?index=${encodeURIComponent(index)}`);
}

export async function fetchEvents(): Promise<EventsResponse> {
  return http<EventsResponse>("/api/events");
}

export async function refreshPrices(): Promise<PriceRefreshResponse> {
  return http<PriceRefreshResponse>("/api/prices/refresh", { method: "POST" });
}

/** Register this device's native push token (mobile only — see lib/push.ts). */
export async function registerPushToken(
  token: string,
  platform: "ios" | "android" | "web",
): Promise<{ ok: boolean }> {
  return http<{ ok: boolean }>("/api/push/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, platform }),
  });
}

/** Send a test push to the signed-in user's devices (dry-run without FCM creds). */
export async function sendTestPush(): Promise<{ sent: number; dry_run: boolean }> {
  return http<{ sent: number; dry_run: boolean }>("/api/push/test", { method: "POST" });
}

export async function sendChat(messages: ChatMessage[]): Promise<ChatResponse> {
  return http<ChatResponse>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
}

export type ChatStreamEvent =
  | { type: "delta"; text: string }
  | { type: "guardrail" }
  | { type: "replace"; text: string }
  | { type: "done"; guardrail_triggered: boolean; model: string; grounding: ChatGrounding | null }
  | { type: "error"; detail: string };

/**
 * POST /api/chat/stream and invoke `onEvent` for each server-sent event.
 * Parses the `data: {json}\n\n` SSE frames from the response body stream.
 */
export async function sendChatStream(
  messages: ChatMessage[],
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  const token = getAuthToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${getApiUrl()}/api/chat/stream`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify({ messages }),
  });
  if (!res.ok || !res.body) {
    const detail = await res.text();
    throw new Error(`API ${res.status} /api/chat/stream: ${detail}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const line = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      onEvent(JSON.parse(line.slice(5).trim()) as ChatStreamEvent);
    }
  }
}

export async function uploadCsv(file: File): Promise<IngestResult> {
  const formData = new FormData();
  formData.append("file", file);
  return http<IngestResult>("/api/ingest", {
    method: "POST",
    body: formData,
  });
}

export async function previewCsv(file: File): Promise<IngestPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return http<IngestPreviewResponse>("/api/ingest/preview", {
    method: "POST",
    body: formData,
  });
}
