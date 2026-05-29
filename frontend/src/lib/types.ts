export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Archive {
  id: string;
  filename: string;
  status: "pending" | "processing" | "completed" | "failed";
  total_emails: number;
  processed_emails: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmailListItem {
  id: string;
  sender: string;
  subject: string;
  sent_at?: string | null;
  summary?: string | null;
  thread_id?: string | null;
}

export interface EmailDetail extends EmailListItem {
  archive_id: string;
  thread_id?: string | null;
  message_id?: string | null;
  in_reply_to?: string | null;
  source_file?: string | null;
  receivers: string[];
  cc: string[];
  body_text: string;
  created_at: string;
  thread_subject?: string | null;
  similar_emails: SimilarEmail[];
}

export interface SimilarEmail {
  id: string;
  subject: string;
  sender: string;
  sent_at?: string | null;
  similarity_score: number;
  summary?: string | null;
}

export interface SearchHit {
  id: string;
  subject: string;
  sender: string;
  sent_at?: string | null;
  summary?: string | null;
  snippet: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchHit[];
}

export interface AnalyticsDashboard {
  overview: {
    total_emails: number;
    total_threads: number;
    total_archives: number;
    unique_senders: number;
    unique_receivers: number;
    emails_with_summary: number;
    date_range_start?: string | null;
    date_range_end?: string | null;
  };
  top_senders: { sender: string; count: number }[];
  daily_volume: { date: string; count: number }[];
  top_subjects: { keyword: string; count: number }[];
  thread_size_distribution: Record<string, number>;
}

export interface HealthResponse {
  status: string;
  database: { status: string; database?: string; version?: string };
  elasticsearch: { status: string; document_count?: number; cluster_status?: string };
  chromadb: { status: string; document_count?: number; mode?: string; embedding_model?: string };
}

export interface Thread {
  id: string;
  subject_normalized: string;
  participant_count: number;
  email_count: number;
  first_email_at?: string | null;
  last_email_at?: string | null;
  summary?: string | null;
  emails: EmailListItem[];
}
