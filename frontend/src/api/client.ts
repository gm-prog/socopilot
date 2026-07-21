<<<<<<< HEAD
import type { z } from "zod";

import { apiUrl } from "../config/api";
import { fetchWithAuth, getStoredAccessToken } from "./auth";
import { ApiError } from "./errors";
import { useNotificationStore } from "../store/notificationStore";
import {
  formatZodIssues,
  reportValidationError,
} from "../lib/validation/reportValidationError";

export { fetchWithAuth } from "./auth";

function authHeaders(): HeadersInit {
  const token = getStoredAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function ensureOk(res: Response, fallbackMessage: string): Promise<void> {
  if (res.ok) return;
  let detail = "";
  try {
    const body = await res.json();
    detail = body.detail || "";
  } catch {
    // response body not JSON
  }
  throw new Error(detail ? `${fallbackMessage}: ${detail}` : `${fallbackMessage}: ${res.status}`);
}

export interface ApiRequestOptions {
  /** Skip global error toast (caller handles errors) */
  silent?: boolean;
  /** Skip response body Zod validation */
  skipValidation?: boolean;
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg).join(", ");
    }
  } catch {
    // ignore parse failures
  }
  return `Request failed (${res.status})`;
}

/**
 * Authenticated JSON request with optional Zod response validation.
 * Auth token injection + 401 refresh handled by fetchWithAuth.
 */
export async function apiRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  init: RequestInit = {},
  options: ApiRequestOptions = {}
): Promise<T> {
  const url = path.startsWith("http") ? path : apiUrl(path);

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init.body ? { "Content-Type": "application/json" } : {}),
    ...(init.headers as Record<string, string> | undefined),
  };

  let response: Response;
  try {
    response = await fetchWithAuth(url, { ...init, headers });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Network request failed";
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, 0, path);
  }

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, response.status, path);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  let json: unknown;
  try {
    json = await response.json();
  } catch {
    const message = "Invalid JSON response from server";
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, response.status, path);
  }

  if (options.skipValidation) {
    return json as T;
  }

  const parsed = schema.safeParse(json);
  if (!parsed.success) {
    const detail = formatZodIssues(parsed.error.issues);
    reportValidationError({
      source: "api",
      message: `Response schema mismatch: ${path}`,
      issues: parsed.error.issues,
    });
    const message = `Server returned unexpected data (${detail})`;
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, response.status, path, parsed.error);
  }

  return parsed.data;
}

export function apiGet<T>(
  path: string,
  schema: z.ZodType<T>,
  options?: ApiRequestOptions
): Promise<T> {
  return apiRequest(path, schema, { method: "GET" }, options);
}

export function apiPost<T>(
  path: string,
  schema: z.ZodType<T>,
  body: unknown,
  options?: ApiRequestOptions
): Promise<T> {
  return apiRequest(
    path,
    schema,
    { method: "POST", body: JSON.stringify(body) },
    options
  );
}

export function apiPatch<T>(
  path: string,
  schema: z.ZodType<T>,
  body: unknown,
  options?: ApiRequestOptions
): Promise<T> {
  return apiRequest(
    path,
    schema,
    { method: "PATCH", body: JSON.stringify(body) },
    options
  );
}

/** Unauthenticated health probes */
export async function fetchHealth(): Promise<{
  status: string;
  service: string;
  version: string;
}> {
  const res = await fetch(apiUrl("/api/v1/health"));
  await ensureOk(res, "Health check failed");
  return res.json();
}

export async function fetchReadiness(): Promise<{
  status: string;
  checks: Array<{ name: string; status: string; detail?: string }>;
}> {
  const res = await fetch(apiUrl("/api/v1/ready"));
  await ensureOk(res, "Readiness check failed");
  return res.json();
}

export async function fetchSystemInfo(): Promise<Record<string, unknown>> {
  const res = await fetch(apiUrl("/api/v1/system/info"), { headers: authHeaders() });
  await ensureOk(res, "System info failed");
  return res.json();
}

export async function fetchOllamaStatus(): Promise<Record<string, unknown>> {
  const res = await fetch(apiUrl("/api/v1/system/ollama/status"), { headers: authHeaders() });
  await ensureOk(res, "Ollama status failed");
  return res.json();
}
=======
import type { z } from "zod";

import { apiUrl } from "../config/api";
import { fetchWithAuth } from "./auth";
import { ApiError } from "./errors";
import { useNotificationStore } from "../store/notificationStore";
import {
  formatZodIssues,
  reportValidationError,
} from "../lib/validation/reportValidationError";

export { fetchWithAuth } from "./auth";

export interface ApiRequestOptions {
  /** Skip global error toast (caller handles errors) */
  silent?: boolean;
  /** Skip response body Zod validation */
  skipValidation?: boolean;
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg).join(", ");
    }
  } catch {
    // ignore parse failures
  }
  return `Request failed (${res.status})`;
}

/**
 * Authenticated JSON request with optional Zod response validation.
 * Auth token injection + 401 refresh handled by fetchWithAuth.
 */
export async function apiRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  init: RequestInit = {},
  options: ApiRequestOptions = {}
): Promise<T> {
  const url = path.startsWith("http") ? path : apiUrl(path);

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init.body ? { "Content-Type": "application/json" } : {}),
    ...(init.headers as Record<string, string> | undefined),
  };

  let response: Response;
  try {
    response = await fetchWithAuth(url, { ...init, headers });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Network request failed";
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, 0, path);
  }

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, response.status, path);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  let json: unknown;
  try {
    json = await response.json();
  } catch {
    const message = "Invalid JSON response from server";
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, response.status, path);
  }

  if (options.skipValidation) {
    return json as T;
  }

  const parsed = schema.safeParse(json);
  if (!parsed.success) {
    const detail = formatZodIssues(parsed.error.issues);
    reportValidationError({
      source: "api",
      message: `Response schema mismatch: ${path}`,
      issues: parsed.error.issues,
    });
    const message = `Server returned unexpected data (${detail})`;
    if (!options.silent) {
      useNotificationStore.getState().pushError(message);
    }
    throw new ApiError(message, response.status, path, parsed.error);
  }

  return parsed.data;
}

export function apiGet<T>(
  path: string,
  schema: z.ZodType<T>,
  options?: ApiRequestOptions
): Promise<T> {
  return apiRequest(path, schema, { method: "GET" }, options);
}

export function apiPost<T>(
  path: string,
  schema: z.ZodType<T>,
  body: unknown,
  options?: ApiRequestOptions
): Promise<T> {
  return apiRequest(
    path,
    schema,
    { method: "POST", body: JSON.stringify(body) },
    options
  );
}

export function apiPatch<T>(
  path: string,
  schema: z.ZodType<T>,
  body: unknown,
  options?: ApiRequestOptions
): Promise<T> {
  return apiRequest(
    path,
    schema,
    { method: "PATCH", body: JSON.stringify(body) },
    options
  );
}

/** Unauthenticated health probes */
export async function fetchHealth(): Promise<{
  status: string;
  service: string;
  version: string;
}> {
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
>>>>>>> 1d16aa5 (feat: semantic search, real-time alerts, and frontend store migration)
