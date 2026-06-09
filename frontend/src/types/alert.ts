import type { z } from "zod";

import {
  AlertDetailSchema,
  AlertIOCSchema,
  AlertListResponseSchema,
  AlertSummarySchema,
  EnrichmentResultSchema,
} from "../schemas/alert";

/** Inferred types — single source of truth aligned with backend Pydantic schemas */
export type AlertSummary = z.infer<typeof AlertSummarySchema>;
export type AlertIOC = z.infer<typeof AlertIOCSchema>;
export type AlertDetail = z.infer<typeof AlertDetailSchema>;
export type EnrichmentResult = z.infer<typeof EnrichmentResultSchema>;
export type AlertListResponse = z.infer<typeof AlertListResponseSchema>;

export {
  AlertSummarySchema,
  AlertDetailSchema,
  AlertIOCSchema,
  AlertListResponseSchema,
  EnrichmentResultSchema,
  EnrichmentResultListSchema,
  WebSocketAlertPayloadSchema,
  WebSocketNewAlertFrameSchema,
} from "../schemas/alert";
