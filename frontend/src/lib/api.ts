import type {
  AnalyticsDashboard,
  Archive,
  EmailDetail,
  EmailListItem,
  HealthResponse,
  PaginatedResponse,
  SearchResponse,
  SimilarEmail,
  Thread,
} from "./types";

function normalizeApiBase(raw: string): string {
  const trimmed = raw.replace(/\/$/, "");
  return trimmed.endsWith("/api/v1") ? trimmed : `${trimmed}/api/v1`;
}

function getApiBase(): string {
  if (typeof window !== "undefined") {
    return "/api/v1";
  }

  const serverBase =
    process.env.INTERNAL_API_URL ||
    process.env.BACKEND_INTERNAL_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000/api/v1";

  return normalizeApiBase(serverBase);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${getApiBase()}${path}`, {
      ...options,
      headers: {
        ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...options?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new Error(
      "Cannot reach the API. Check that the backend is running and NEXT_PUBLIC_API_URL / rewrites are configured."
    );
  }

  if (!response.ok) {
    const errorText = await response.text();
    let detail = errorText || `Request failed: ${response.status}`;
    try {
      const parsed = JSON.parse(errorText) as { detail?: string };
      if (parsed.detail) detail = parsed.detail;
    } catch {
      /* use raw text */
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  listArchives: (page = 1) =>
    request<PaginatedResponse<Archive>>(`/uploads?page=${page}&page_size=10`),

  uploadArchive: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<{ archive: Archive; message: string }>("/uploads", {
      method: "POST",
      body: formData,
    });
  },

  listEmails: (page = 1, sender?: string) => {
    const params = new URLSearchParams({ page: String(page), page_size: "15" });
    if (sender) params.set("sender", sender);
    return request<PaginatedResponse<EmailListItem>>(`/emails?${params}`);
  },

  getEmail: (id: string) => request<EmailDetail>(`/emails/${id}`),

  listThreads: (page = 1) =>
    request<PaginatedResponse<Thread>>(`/emails/threads?page=${page}&page_size=10`),

  keywordSearch: (query: string, page = 1) =>
    request<SearchResponse>("/search/keyword", {
      method: "POST",
      body: JSON.stringify({ query, page, page_size: 15 }),
    }),

  semanticSearch: (query: string, topK = 10) =>
    request<SearchResponse>("/search/semantic", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK, min_score: 0.0 }),
    }),

  similarEmails: (emailId: string, topK = 5) =>
    request<SimilarEmail[]>(`/search/similar/${emailId}?top_k=${topK}`),

  getAnalytics: () => request<AnalyticsDashboard>("/analytics/dashboard"),
};
