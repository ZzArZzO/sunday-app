import type {
  BriefingResponse,
  IngestResult,
  PortfolioResponse,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
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

export async function uploadCsv(file: File): Promise<IngestResult> {
  const formData = new FormData();
  formData.append("file", file);
  return http<IngestResult>("/api/ingest", {
    method: "POST",
    body: formData,
  });
}
