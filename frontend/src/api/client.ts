import { apiUrl } from "../config/api";

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
