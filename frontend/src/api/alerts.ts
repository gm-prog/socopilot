import { z } from "zod";

import { apiGet, apiPatch, apiPost } from "./client";
import {
  AlertDetailSchema,
  AlertListResponseSchema,
  EnrichmentResultListSchema,
} from "../schemas/alert";
import type { AlertDetail, AlertListResponse, EnrichmentResult } from "../types/alert";

export interface FetchAlertsParams {
  page?: number;
  page_size?: number;
  severity?: string;
  lifecycle_state?: string;
}

export async function fetchAlerts(
  params?: FetchAlertsParams
): Promise<AlertListResponse> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  if (params?.severity) qs.set("severity", params.severity);
  if (params?.lifecycle_state) qs.set("lifecycle_state", params.lifecycle_state);

  const query = qs.toString();
  const path = query ? `/api/v1/alerts?${query}` : "/api/v1/alerts";

  return apiGet(path, AlertListResponseSchema);
}

export async function fetchAlert(id: string): Promise<AlertDetail> {
  return apiGet(`/api/v1/alerts/${id}`, AlertDetailSchema);
}

export async function fetchAlertEnrichment(
  alertId: string
): Promise<EnrichmentResult[]> {
  try {
    return await apiGet(
      `/api/v1/enrichment/alerts/${alertId}`,
      EnrichmentResultListSchema,
      { silent: true }
    );
  } catch (err) {
    // Enrichment is optional — empty list on failure
    return [];
  }
}

export async function updateAlertWorkflow(
  alertId: string,
  body: {
    lifecycle_state?: string;
    analyst_notes?: string;
    tags?: string[];
  }
): Promise<AlertDetail> {
  return apiPatch(`/api/v1/alerts/${alertId}`, AlertDetailSchema, body);
}

const SemanticSearchResponseSchema = z.object({
  results: z.array(
    z.object({
      alert_id: z.string().uuid(),
      score: z.number(),
      title: z.string().nullable().optional(),
    })
  ),
  message: z.string().optional(),
});

export async function semanticSearch(query: string, limit = 10) {
  return apiPost(
    "/api/v1/search/semantic",
    SemanticSearchResponseSchema,
    { query, limit }
  );
}
