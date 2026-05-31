/**
 * API base URL for fetch calls.
 *
 * Docker: use host.docker.internal to reach backend from frontend container.
 * Vite dev: set VITE_API_BASE_URL=http://localhost:8000 or use vite proxy with empty base.
 */
export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalized}`;
}

export function websocketUrl(
  path: string,
  params?: Record<string, string | null | undefined>,
): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const origin =
    API_BASE || (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");
  const url = new URL(normalized, origin);

  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";

  for (const [key, value] of Object.entries(params ?? {})) {
    if (value) {
      url.searchParams.set(key, value);
    }
  }

  return url.toString();
}
