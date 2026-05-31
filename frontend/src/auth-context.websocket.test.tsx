import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import React, { useEffect, useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { useAlertsStream } from "./hooks/useAlertsStream";
import { WebSocketManager } from "./lib/websocketManager";
import { fetchWithAuth } from "./api/auth";
import { MockWebSocketServer } from "./tests/mockWebSocket";
import { createExpiringJwt, createFetchMock, flushPromises } from "./tests/authTestUtils";

function AuthStatusDisplay() {
    const { status, isAuthenticated } = useAuth();
    return (
        <div>
            <span data-testid="auth-status">{status}</span>
            <span data-testid="auth-flag">{isAuthenticated ? "true" : "false"}</span>
        </div>
    );
}

function AuthStatusTracker({ onStatus }: { onStatus: (status: string) => void }) {
    const { status } = useAuth();
    useEffect(() => {
        onStatus(status);
    }, [onStatus, status]);
    return null;
}

function AlertsStreamWatcher({ enabled = true }: { enabled?: boolean }) {
    const { isConnected, refetch } = useAlertsStream({ enabled, maxQueueSize: 10 });
    return (
        <div>
            <span data-testid="ws-connected">{isConnected ? "yes" : "no"}</span>
            <button type="button" onClick={refetch} data-testid="refetch-button">
                refetch
            </button>
        </div>
    );
}

function createResponse(body: unknown, status = 200) {
    return new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
    });
}

describe("SOCopilot auth and websocket resilience", () => {
    let server: MockWebSocketServer;

    beforeEach(() => {
        server = new MockWebSocketServer();
        (globalThis as any).WebSocket = class {
            constructor(url: string) {
                return server.connect(url) as unknown as WebSocket;
            }
        } as unknown as typeof WebSocket;
        window.localStorage.clear();
    });

    afterEach(() => {
        cleanup();
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    it("restores session on startup from a valid persisted token", async () => {
        const token = createExpiringJwt(3600);
        window.localStorage.setItem("socopilot_access_token", token);
        const fetchMock = createFetchMock([
            {
                matcher: (url) => url.endsWith("/api/v1/auth/me"),
                handler: async () => createResponse({ id: "user-1", email: "test@example.com", role: "analyst", tenant_id: "tenant-1" }),
            },
        ]);
        globalThis.fetch = fetchMock as unknown as typeof fetch;

        render(
            <AuthProvider>
            <AuthStatusDisplay />
            </AuthProvider>,
        );

        await waitFor(() => expect(screen.getByTestId("auth-status").textContent).toBe("authenticated"));
        expect(screen.getByTestId("auth-flag").textContent).toBe("true");
        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("rejects expired persisted token and refreshes before hydration", async () => {
        const expiredToken = createExpiringJwt(-60);
        window.localStorage.setItem("socopilot_access_token", expiredToken);
        const refreshedToken = createExpiringJwt(3600);

        let meCallCount = 0;
        const sequence = [
            {
                matcher: (url: string) => url.endsWith("/api/v1/auth/me") && meCallCount === 0,
                handler: async () => {
                    meCallCount += 1;
                    return createResponse({ detail: "Unauthorized" }, 401);
                },
            },
            {
                matcher: (url: string) => url.endsWith("/api/v1/auth/refresh"),
                handler: async () => createResponse({ access_token: refreshedToken }),
            },
            {
                matcher: (url: string) => url.endsWith("/api/v1/auth/me") && meCallCount > 0,
                handler: async () => createResponse({ id: "user-1", email: "test@example.com", role: "analyst", tenant_id: "tenant-1" }),
            },
        ];

        const fetchSequence = vi.fn(async (input: RequestInfo, init?: RequestInit) => {
            const url = typeof input === "string" ? input : input.url;
            const route = sequence.find((routeDef) => routeDef.matcher(url, init));
            if (!route) {
                throw new Error(`Unexpected fetch call to ${url}`);
            }
            return route.handler(url, init);
        });
        globalThis.fetch = fetchSequence as unknown as typeof fetch;

        render(
            <AuthProvider>
            <AuthStatusDisplay />
            </AuthProvider>,
        );

        await waitFor(() => expect(screen.getByTestId("auth-status").textContent).toBe("authenticated"));
        expect(fetchSequence).toHaveBeenCalled();
        expect(window.localStorage.getItem("socopilot_access_token")).toBe(refreshedToken);
    });

    it("does not open websocket before auth is restored and recovers stale corrupted storage", async () => {
        window.localStorage.setItem("socopilot_access_token", "corrupted.token.value");
        const refreshedToken = createExpiringJwt(3600);
        globalThis.fetch = createFetchMock([
            {
                matcher: (url) => url.endsWith("/api/v1/auth/refresh"),
                handler: async () => createResponse({ access_token: refreshedToken }),
            },
            {
                matcher: (url) => url.endsWith("/api/v1/auth/me"),
                handler: async () => createResponse({ id: "user-1", email: "test@example.com", role: "analyst", tenant_id: "tenant-1" }),
            },
        ]);

        render(
            <AuthProvider>
                <AuthStatusDisplay />
                <AlertsStreamWatcher />
            </AuthProvider>,
        );

        expect(server.activeConnections).toBe(0);
        await flushPromises();
        await waitFor(() => expect(screen.getByTestId("auth-status").textContent).toBe("authenticated"));
        expect(server.activeConnections).toBe(1);
    });

    it("executes auth state transitions without stale leaks or duplicate events", async () => {
        const tokenA = createExpiringJwt(3600);
        const tokenB = createExpiringJwt(7200);
        const transitions: string[] = [];
        const fetchMock = createFetchMock([
            {
                matcher: (url) => url.endsWith("/api/v1/auth/me"),
                handler: async () => createResponse({ id: "user-1", email: "test@example.com", role: "analyst", tenant_id: "tenant-1" }),
            },
            {
                matcher: (url) => url.endsWith("/api/v1/auth/login"),
                handler: async () => createResponse({ access_token: tokenA }),
            },
            {
                matcher: (url) => url.endsWith("/api/v1/auth/refresh"),
                handler: async () => createResponse({ access_token: tokenB }),
            },
            {
                matcher: (url) => url.endsWith("/api/v1/auth/logout"),
                handler: async () => createResponse({ detail: "Session revoked" }),
            },
        ]);
        globalThis.fetch = fetchMock;

        const LoggedStatus = () => {
            const auth = useAuth();
            useEffect(() => {
                transitions.push(auth.status);
            }, [auth.status]);
            return null;
        };

        function TestHarness() {
            const auth = useAuth();
            return (
                <>
                    <LoggedStatus />
                    <button data-testid="login" onClick={() => auth.login("admin@test.com", "admin123")}>login</button>
                    <button data-testid="refresh" onClick={() => auth.refreshSession()}>refresh</button>
                    <button data-testid="logout" onClick={() => auth.logout()}>logout</button>
                </>
            );
        }

        render(
            <AuthProvider>
                <TestHarness />
            </AuthProvider>,
        );

        await act(async () => {
            await flushPromises();
        });

        await act(async () => {
            screen.getByTestId("login").click();
            await flushPromises();
        });

await waitFor(() => expect(transitions).toContain("authenticated"));

await act(async () => {
    screen.getByTestId("refresh").click();
    await flushPromises();
});

await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/auth/refresh"), expect.anything()));

await act(async () => {
    screen.getByTestId("logout").click();
    await flushPromises();
});

expect(transitions.filter((state) => state === "authenticated").length).toBeGreaterThan(0);
expect(transitions.filter((state) => state === "unauthenticated").length).toBeGreaterThan(0);
  });

it("enforces a single active websocket and cleans up stale sockets", async () => {
    vi.useFakeTimers();
    const manager = new WebSocketManager({
        getUrl: () => "wss://example.com/ws/alerts",
        getToken: () => createExpiringJwt(3600),
        createWebSocket: (url) => server.connect(url) as unknown as WebSocket,
        onOpen: () => { },
        onClose: () => { },
        onReconnectAttempt: () => { },
        onAuthFailure: async () => false,
    });

    manager.start();
    await flushPromises();
    expect(server.activeConnections).toBe(1);
    expect(manager.state.activeSocketCount).toBe(1);

    server.disconnectAll(1000, "normal");
    await flushPromises();
    expect(server.activeConnections).toBe(0);
    expect(manager.state.activeSocketCount).toBe(0);

    vi.runOnlyPendingTimers();
    await flushPromises();
    expect(server.activeConnections).toBe(0);
});

it("reconnects with backoff after unexpected socket closure and avoids duplicate sockets", async () => {
    vi.useFakeTimers();
    const reconnectCalls: Array<{ attempt: number; delay: number }> = [];
    const manager = new WebSocketManager({
        getUrl: () => "wss://example.com/ws/alerts",
        getToken: () => createExpiringJwt(3600),
        createWebSocket: (url) => server.connect(url) as unknown as WebSocket,
        onReconnectAttempt: (attempt, delay) => reconnectCalls.push({ attempt, delay }),
        onAuthFailure: async () => false,
    });

    manager.start();
    await flushPromises();
    expect(server.activeConnections).toBe(1);

    server.disconnectAll(4000, "network failure");
    await flushPromises();
    expect(reconnectCalls.length).toBe(1);
    expect(manager.state.activeSocketCount).toBe(0);

    vi.runOnlyPendingTimers();
    await flushPromises();
    expect(manager.state.activeSocketCount).toBe(1);
    expect(server.connectionCount).toBeGreaterThanOrEqual(2);
});

it("performs a single refresh for multiple concurrent 401 requests", async () => {
    const expiredToken = createExpiringJwt(-120);
    window.localStorage.setItem("socopilot_access_token", expiredToken);
    const freshToken = createExpiringJwt(3600);
    let refreshCount = 0;

    const fetchMock = vi.fn(async (input: RequestInfo, init?: RequestInit) => {
        const url = typeof input === "string" ? input : input.url;
        if (url.endsWith("/api/v1/auth/refresh")) {
            refreshCount += 1;
            return createResponse({ access_token: freshToken });
        }
        if (url.endsWith("/api/v1/alerts")) {
            if (init?.headers && (init.headers as Record<string, string>).Authorization?.includes("Bearer ")) {
                return createResponse({ items: [] });
            }
            return createResponse({ detail: "Unauthorized" }, 401);
        }
        return createResponse({ detail: "not found" }, 404);
    });

    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const promises = [
        fetchWithAuth("/api/v1/alerts"),
        fetchWithAuth("/api/v1/alerts"),
    ];

    await act(async () => {
        await Promise.all(promises);
    });

    expect(refreshCount).toBe(1);
});

it("clears state and timers after forced logout with no zombie reconnects", async () => {
    vi.useFakeTimers();
    const manager = new WebSocketManager({
        getUrl: () => "wss://example.com/ws/alerts",
        getToken: () => createExpiringJwt(3600),
        createWebSocket: (url) => server.connect(url) as unknown as WebSocket,
        onAuthFailure: async () => false,
    });

    manager.start();
    await flushPromises();
    server.disconnectAll(4000, "network failure");
    await flushPromises();
    expect(manager.state.reconnectAttempts).toBe(1);

    manager.stop();
    vi.runOnlyPendingTimers();
    expect(server.activeConnections).toBe(0);
    expect(manager.state.hasPendingReconnect).toBe(false);
});

it("synchronizes logout and refresh events across tabs via auth broadcast events", async () => {
    const token = createExpiringJwt(3600);
    const fetchMock = createFetchMock([
        {
            matcher: (url) => url.endsWith("/api/v1/auth/me"),
            handler: async () => createResponse({ id: "user-1", email: "test@example.com", role: "analyst", tenant_id: "tenant-1" }),
        },
    ]);
    globalThis.fetch = fetchMock;

    render(
        <AuthProvider>
            <AuthStatusDisplay />
        </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("auth-status").textContent).toBe("unauthenticated"));

    act(() => {
        window.localStorage.setItem("socopilot_access_token", token);
        window.dispatchEvent(new CustomEvent("socopilot-auth-event", { detail: { action: "login", timestamp: Date.now() } }));
    });

    await waitFor(() => expect(screen.getByTestId("auth-status").textContent).toBe("authenticated"));

    act(() => {
        window.dispatchEvent(new CustomEvent("socopilot-auth-event", { detail: { action: "logout", timestamp: Date.now() } }));
    });

    await waitFor(() => expect(screen.getByTestId("auth-status").textContent).toBe("unauthenticated"));
});

it("cleans up auth event listeners on unmount", async () => {
    const addSpy = vi.spyOn(window, "addEventListener");
    const removeSpy = vi.spyOn(window, "removeEventListener");
    const { unmount } = render(
        <AuthProvider>
        <AuthStatusDisplay />
        </AuthProvider>,
    );
    await flushPromises();
    expect(addSpy).toHaveBeenCalledWith("storage", expect.any(Function));
    expect(addSpy).toHaveBeenCalledWith("socopilot-auth-event", expect.any(Function));
    unmount();
    expect(removeSpy).toHaveBeenCalledWith("storage", expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith("socopilot-auth-event", expect.any(Function));
});
});
