import { beforeEach, describe, expect, it, vi } from "vitest";
import {
    clearStoredAccessToken,
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
});
