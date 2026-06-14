import type {
  BenchmarkResponse,
  BriefingResponse,
  ChatGrounding,
  ChatMessage,
  ChatResponse,
  DividendResponse,
  FireResponse,
  IngestPreviewResponse,
  IngestResult,
  PortfolioResponse,
  PriceRefreshResponse,
  RebalanceResponse,
  TaxSummaryResponse,
} from "@/lib/types";

function getApiUrl(): string {
  if (typeof window === "undefined") {
    return process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${getApiUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });
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

export async function fetchFire(): Promise<FireResponse> {
  return http<FireResponse>("/api/fire");
}

export async function fetchDividend(): Promise<DividendResponse> {
  return http<DividendResponse>("/api/dividend");
}

export async function fetchTax(): Promise<TaxSummaryResponse> {
  return http<TaxSummaryResponse>("/api/tax");
}

export async function fetchRebalance(): Promise<RebalanceResponse> {
  return http<RebalanceResponse>("/api/rebalance");
}

export async function fetchBenchmark(index: string): Promise<BenchmarkResponse> {
  return http<BenchmarkResponse>(`/api/benchmark?index=${encodeURIComponent(index)}`);
}

export async function refreshPrices(): Promise<PriceRefreshResponse> {
  return http<PriceRefreshResponse>("/api/prices/refresh", { method: "POST" });
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
  const res = await fetch(`${getApiUrl()}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
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
