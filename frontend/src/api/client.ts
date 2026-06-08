import { apiUrl } from "../config/api";

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

export async function fetchHealth(): Promise<{ status: string; service: string; version: string }> {
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
  const res = await fetch(apiUrl("/api/v1/system/info"));
  await ensureOk(res, "System info failed");
  return res.json();
}

export async function fetchOllamaStatus(): Promise<Record<string, unknown>> {
  const res = await fetch(apiUrl("/api/v1/system/ollama/status"));
  await ensureOk(res, "Ollama status failed");
  return res.json();
}
