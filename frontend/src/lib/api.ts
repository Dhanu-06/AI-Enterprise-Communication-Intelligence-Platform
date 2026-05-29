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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
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
