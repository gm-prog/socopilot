import { apiUrl } from "../config/api";

const ACCESS_TOKEN_KEY = "socopilot_access_token";
const AUTH_BROADCAST_KEY = "socopilot_auth_broadcast";
const AUTH_EVENT_NAME = "socopilot-auth-event";

export type AuthBroadcastAction = "login" | "logout" | "token_update";

export interface AuthBroadcastMessage {
  action: AuthBroadcastAction;
  timestamp: number;
}

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  tenant_id: string;
}

const isBrowser = typeof window !== "undefined";

function safeJsonParse<T>(value: string | null): T | null {
  if (!value) return null;
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const decoded = atob(payload);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

function normalizeHeaders(headers: HeadersInit | undefined): Record<string, string> {
  if (!headers) return {};
  if (headers instanceof Headers) {
    return Object.fromEntries(Array.from(headers.entries()));
  }
  if (Array.isArray(headers)) {
    return Object.fromEntries(headers);
  }
  return Object.fromEntries(Object.entries(headers) as [string, string][]);
}

function getRequestUrl(input: RequestInfo): string {
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.toString();
  }
  return input.url;
}

function handleRefreshRouteUnauthorized(input: RequestInfo): void {
  const requestUrl = getRequestUrl(input);
  if (!requestUrl.includes("/auth/refresh")) {
    return;
  }

  try {
    window.localStorage.clear();
    window.sessionStorage.clear();
  } catch {
    // ignore storage failures
  }

  window.location.href = "/login";
}

export function getStoredAccessToken(): string | null {
  if (!isBrowser) return null;
  try {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function persistAccessToken(token: string | null, action: AuthBroadcastAction = token ? "login" : "logout"): void {
  if (!isBrowser) return;
  try {
    if (token) {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
    } else {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    }
    const payload: AuthBroadcastMessage = { action, timestamp: Date.now() };
    window.localStorage.setItem(AUTH_BROADCAST_KEY, JSON.stringify(payload));
    window.dispatchEvent(new CustomEvent(AUTH_EVENT_NAME, { detail: payload }));
  } catch {
    // ignore storage failures
  }
}

export function clearStoredAccessToken(): void {
  persistAccessToken(null, "logout");
}

export function subscribeToAuthEvents(
  listener: (payload: AuthBroadcastMessage) => void,
): () => void {
  if (!isBrowser) return () => { };

  const storageHandler = (event: StorageEvent) => {
    if (event.key !== AUTH_BROADCAST_KEY) return;
    const payload = safeJsonParse<AuthBroadcastMessage>(event.newValue);
    if (payload) listener(payload);
  };

  const customHandler = (event: Event) => {
    const custom = event as CustomEvent<AuthBroadcastMessage>;
    if (!custom.detail) return;
    listener(custom.detail);
  };

  window.addEventListener("storage", storageHandler);
  window.addEventListener(AUTH_EVENT_NAME, customHandler as EventListener);

  return () => {
    window.removeEventListener("storage", storageHandler);
    window.removeEventListener(AUTH_EVENT_NAME, customHandler as EventListener);
  };
}

export function isJwtExpired(token: string, leewaySeconds = 10): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== "number") return true;
  return Date.now() / 1000 >= payload.exp - leewaySeconds;
}

let refreshPromise: Promise<string | null> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const response = await fetch(apiUrl("/api/v1/auth/refresh"), {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        handleRefreshRouteUnauthorized(apiUrl("/api/v1/auth/refresh"));
        return null;
      }

      const body = await response.json();
      const accessToken = body.access_token as string | undefined;
      if (!accessToken) {
        return null;
      }

      persistAccessToken(accessToken, "token_update");
      return accessToken;
    } catch (err) {
      console.warn("[refreshAccessToken] Token refresh failed:", err instanceof Error ? err.message : err);
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  const token = await refreshPromise;
  if (!token) {
    clearStoredAccessToken();
  }
  return token;
}

export async function loginRequest(email: string, password: string): Promise<string> {
  const response = await fetch(apiUrl("/api/v1/auth/login"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Login failed");
  }

  const body = await response.json();
  const accessToken = body.access_token as string | undefined;
  if (!accessToken) {
    throw new Error("Missing access token");
  }

  return accessToken;
}

export async function logoutRequest(): Promise<void> {
  const response = await fetch(apiUrl("/api/v1/auth/logout"), {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    console.warn(`[logoutRequest] Server returned ${response.status}`);
  }
}

export async function fetchProfile(accessToken: string): Promise<UserProfile | null> {
  try {
    const response = await fetch(apiUrl("/api/v1/auth/me"), {
      credentials: "include",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    if (!response.ok) {
      console.warn(`[fetchProfile] Server returned ${response.status}`);
      return null;
    }
    return (await response.json()) as UserProfile;
  } catch (err) {
    console.warn("[fetchProfile] Failed:", err instanceof Error ? err.message : err);
    return null;
  }
}

export async function fetchWithAuth(
  input: RequestInfo,
  init: RequestInit = {},
  options: { retry?: boolean } = { retry: true },
): Promise<Response> {
  const requestHeaders = normalizeHeaders(init.headers);
  let token = getStoredAccessToken();

  if (token && isJwtExpired(token, 30)) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      token = refreshed;
    }
  }

  const headers = {
    ...requestHeaders,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(input, {
    ...init,
    credentials: "include",
    headers,
  });

  if (response.status === 401 && getRequestUrl(input).includes("/auth/refresh")) {
    handleRefreshRouteUnauthorized(input);
    return response;
  }

  if (response.status !== 401 || options.retry === false) {
    return response;
  }

  const refreshedToken = await refreshAccessToken();
  if (!refreshedToken) {
    return response;
  }

  const retryHeaders = {
    ...requestHeaders,
    Authorization: `Bearer ${refreshedToken}`,
  };

  return fetch(input, {
    ...init,
    credentials: "include",
    headers: retryHeaders,
  });
}

