import { z } from "zod";

import { apiUrl } from "../config/api";
import { fetchWithAuth } from "./auth";
import { ApiError } from "./errors";
import { formatZodIssues, reportValidationError } from "../lib/validation/reportValidationError";

export async function fetchHealth(): Promise<{ status: string; service: string; version: string }> {
  const res = await fetch(apiUrl("/api/v1/health"));
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchReadiness(): Promise<{
  status: string;
  checks: Array<{ name: string; status: string; detail?: string }>;
}> {
  const res = await fetch(apiUrl("/api/v1/ready"));
  if (!res.ok) throw new Error(`Readiness check failed: ${res.status}`);
  return res.json();
}

export async function fetchSystemInfo(): Promise<Record<string, unknown>> {
  const res = await fetch(apiUrl("/api/v1/system/info"));
  if (!res.ok) throw new Error(`System info failed: ${res.status}`);
  return res.json();
}

export async function fetchOllamaStatus(): Promise<Record<string, unknown>> {
  const res = await fetch(apiUrl("/api/v1/system/ollama/status"));
  if (!res.ok) throw new Error(`Ollama status failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Authenticated, schema-validated JSON API helpers
// ---------------------------------------------------------------------------
//
// These were lost when a stripped-down client.ts was restored in commit
// dd9f99e ("fix: restore clean client.ts from master"), which broke the
// production build: src/api/alerts.ts imports apiGet/apiPatch/apiPost.

interface RequestOptions {
  /** Suppress console reporting (used for best-effort calls like enrichment). */
  silent?: boolean;
}

async function request<T>(
  method: "GET" | "POST" | "PATCH" | "DELETE",
  path: string,
  schema: z.ZodType<T>,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetchWithAuth(apiUrl(path), {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const detail: unknown = await response.json().catch(() => null);
    const message =
      detail && typeof detail === "object" && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : `${method} ${path} failed with status ${response.status}`;

    if (!options.silent) {
      // eslint-disable-next-line no-console
      console.error(`[SOCopilot] API error ${response.status} on ${method} ${path}:`, message);
    }
    throw new ApiError(message, response.status, path);
  }

  const data: unknown = await response.json().catch(() => null);
  const result = schema.safeParse(data);

  if (!result.success) {
    reportValidationError({
      source: "api",
      message: `${method} ${path} response failed schema validation: ${formatZodIssues(result.error.issues)}`,
      issues: result.error.issues,
    });
    throw new ApiError(
      `Response from ${method} ${path} failed schema validation`,
      response.status,
      path,
      result.error,
    );
  }

  return result.data;
}

export function apiGet<T>(
  path: string,
  schema: z.ZodType<T>,
  options?: RequestOptions,
): Promise<T> {
  return request("GET", path, schema, undefined, options);
}

export function apiPost<T>(
  path: string,
  schema: z.ZodType<T>,
  body?: unknown,
  options?: RequestOptions,
): Promise<T> {
  return request("POST", path, schema, body, options);
}

export function apiPatch<T>(
  path: string,
  schema: z.ZodType<T>,
  body?: unknown,
  options?: RequestOptions,
): Promise<T> {
  return request("PATCH", path, schema, body, options);
}

export function apiDelete<T>(
  path: string,
  schema: z.ZodType<T>,
  options?: RequestOptions,
): Promise<T> {
  return request("DELETE", path, schema, undefined, options);
}
