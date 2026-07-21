import { beforeEach, describe, expect, it, vi } from "vitest";
import {
    clearStoredAccessToken,
    fetchWithAuth,
    getStoredAccessToken,
    isJwtExpired,
    persistAccessToken,
    subscribeToAuthEvents,
} from "./auth";

describe("auth client", () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it("stores and reads an access token", () => {
        persistAccessToken("token-123", "login");
        expect(getStoredAccessToken()).toBe("token-123");
    });

    it("clears stored token and emits logout events", () => {
        const listener = vi.fn();
        const unsubscribe = subscribeToAuthEvents(listener);

        persistAccessToken("token-abc", "login");
        clearStoredAccessToken();

        expect(getStoredAccessToken()).toBeNull();
        expect(listener).toHaveBeenCalled();

        unsubscribe();
    });

    it("returns true for an expired JWT", () => {
        const expiredToken = `header.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) - 10 }))}.signature`;
        expect(isJwtExpired(expiredToken)).toBe(true);
    });

    it("returns false for a valid JWT", () => {
        const validToken = `header.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))}.signature`;
        expect(isJwtExpired(validToken)).toBe(false);
    });

    it("clears storage and redirects on a 401 from the refresh route", async () => {
        const locationMock = { href: "/dashboard" };
        Object.defineProperty(window, "location", {
            configurable: true,
            value: locationMock,
        });

        localStorage.setItem("keep-me", "1");
        sessionStorage.setItem("session-keep", "1");

        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue(new Response(null, { status: 401, statusText: "Unauthorized" }))
        );

        await fetchWithAuth("/api/v1/auth/refresh", {}, { retry: false });

        expect(localStorage.length).toBe(0);
        expect(sessionStorage.length).toBe(0);
        expect(locationMock.href).toBe("/login");

        vi.unstubAllGlobals();
    });
});
