export interface AlertSummary {
  id: string;
  title: string;
  severity: string;
  status: string;
  lifecycle_state: string;
  source: string;
  detected_at: string;
  ingested_at: string;
  last_seen_at: string;
  duplicate_count: number;
  fingerprint: string;
  time_bucket: string;
  assigned_to: string | null;
  tags: string[];
}

export interface AlertIOC {
  id: string;
  ioc_type: string;
  ioc_value: string;
  confidence: number;
}

export interface EnrichmentResult {
  id: string;
  provider: string;
  status: string;
  summary: Record<string, unknown> | null;
  latency_ms: number | null;
}

export interface AlertDetail extends AlertSummary {
  description: string | null;
  source_event_id: string | null;
  raw_event_id: string | null;
  normalized_payload: Record<string, unknown>;
  raw_payload: Record<string, unknown> | null;
  enrichment_summary: Record<string, unknown> | null;
  analyst_notes: string | null;
  assigned_at: string | null;
  closed_at: string | null;
  iocs: AlertIOC[];
}

export interface AlertListResponse {
  items: AlertSummary[];
  total: number;
  page: number;
  page_size: number;
}
