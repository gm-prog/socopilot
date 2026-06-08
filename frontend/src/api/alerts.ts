import { apiUrl } from "../config/api";
import { fetchWithAuth } from "./auth";
import { ensureOk } from "./client";
import type { AlertDetail, AlertListResponse, EnrichmentResult } from "../types/alert";


export async function fetchAlerts(params?: {
  page?: number;
  page_size?: number;
  severity?: string;
  lifecycle_state?: string;
}): Promise<AlertListResponse> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  if (params?.severity) qs.set("severity", params.severity);
  if (params?.lifecycle_state) qs.set("lifecycle_state", params.lifecycle_state);

  const res = await fetchWithAuth(`${apiUrl("/api/v1/alerts")}?${qs}`);
  await ensureOk(res, "Failed to load alerts");
  return res.json();
}

export async function fetchAlert(id: string): Promise<AlertDetail> {
  const res = await fetchWithAuth(apiUrl(`/api/v1/alerts/${id}`));
  await ensureOk(res, "Failed to load alert");
  return res.json();
}

export async function fetchAlertEnrichment(alertId: string): Promise<EnrichmentResult[]> {
  const res = await fetchWithAuth(apiUrl(`/api/v1/enrichment/alerts/${alertId}`));
  if (res.status === 401) {
    console.warn(`[fetchAlertEnrichment] Unauthorized for alert ${alertId}`);
    return [];
  }
  if (!res.ok) {
    console.warn(`[fetchAlertEnrichment] Failed for alert ${alertId}: ${res.status}`);
    return [];
  }
  return res.json();
}

export async function updateAlertWorkflow(
  alertId: string,
  body: {
    lifecycle_state?: string;
    analyst_notes?: string;
    tags?: string[];
  },
): Promise<AlertDetail> {
  const res = await fetchWithAuth(apiUrl(`/api/v1/alerts/${alertId}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  await ensureOk(res, "Update failed");
  return res.json();
}

export async function semanticSearch(query: string, limit = 10): Promise<unknown> {
  const res = await fetchWithAuth(apiUrl("/api/v1/search/semantic"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  await ensureOk(res, "Search failed");
  return res.json();
}
