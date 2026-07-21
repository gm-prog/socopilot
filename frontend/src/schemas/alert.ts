import { z } from "zod";

/** ISO-8601 datetime string from backend JSON serialization */
const isoDateTime = z.string().min(1);

const uuidString = z.string().uuid();

export const AlertSummarySchema = z.object({
  id: uuidString,
  title: z.string(),
  severity: z.string(),
  status: z.string(),
  lifecycle_state: z.string(),
  source: z.string(),
  detected_at: isoDateTime,
  ingested_at: isoDateTime,
  last_seen_at: isoDateTime,
  duplicate_count: z.number().int(),
  fingerprint: z.string(),
  time_bucket: z.string(),
  assigned_to: uuidString.nullable(),
  tags: z.array(z.string()),
});

export const AlertIOCSchema = z.object({
  id: uuidString,
  ioc_type: z.string(),
  ioc_value: z.string(),
  confidence: z.number(),
});

export const AlertDetailSchema = AlertSummarySchema.extend({
  description: z.string().nullable(),
  source_event_id: z.string().nullable(),
  raw_event_id: uuidString.nullable(),
  normalized_payload: z.record(z.string(), z.unknown()),
  raw_payload: z.record(z.string(), z.unknown()).nullable(),
  enrichment_summary: z.record(z.string(), z.unknown()).nullable(),
  analyst_notes: z.string().nullable(),
  assigned_at: isoDateTime.nullable(),
  closed_at: isoDateTime.nullable(),
  iocs: z.array(AlertIOCSchema),
});

export const AlertListResponseSchema = z.object({
  items: z.array(AlertSummarySchema),
  total: z.number().int().nonnegative().default(0),
  page: z.number().int().positive().default(1),
  page_size: z.number().int().positive().default(50),
});

export const EnrichmentResultSchema = z.object({
  id: uuidString,
  provider: z.string(),
  status: z.string(),
  summary: z.record(z.string(), z.unknown()).nullable(),
  latency_ms: z.number().int().nullable(),
});

export const EnrichmentResultListSchema = z.array(EnrichmentResultSchema);

/** WebSocket envelope published by backend (Redis → WS) */
export const WebSocketNewAlertFrameSchema = z.object({
  type: z.literal("NEW_ALERT"),
  tenant_id: z.string().optional(),
  data: AlertSummarySchema,
});

/** Accept bare alert payloads for backward-compatible clients */
export const WebSocketAlertPayloadSchema = z.union([
  WebSocketNewAlertFrameSchema,
  AlertSummarySchema,
]);

export const AlertWorkflowUpdateSchema = z.object({
  lifecycle_state: z.string().optional(),
  analyst_notes: z.string().optional(),
  tags: z.array(z.string()).optional(),
});

export type AlertSummaryInput = z.input<typeof AlertSummarySchema>;
export type AlertDetailInput = z.input<typeof AlertDetailSchema>;
