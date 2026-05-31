export function createJwt(payload: Record<string, unknown>): string {
    const encode = (value: string) => window.btoa(value).replace(/=+$/, "");
    const header = encode(JSON.stringify({ alg: "HS256", typ: "JWT" }));
    const body = encode(JSON.stringify(payload));
    return `${header}.${body}.signature`;
}

export function createExpiringJwt(secondsFromNow: number): string {
    return createJwt({ exp: Math.floor(Date.now() / 1000) + secondsFromNow, sub: "user-1", role: "analyst" });
}

export interface FetchRouteDefinition {
    matcher: (url: string, init: RequestInit | undefined) => boolean;
    handler: (url: string, init: RequestInit | undefined) => Promise<Response>;
}

export function createFetchMock(routes: FetchRouteDefinition[]) {
    return vi.fn(async (input: RequestInfo, init?: RequestInit) => {
        const url = typeof input === "string" ? input : input.url;
        const route = routes.find((routeDef) => routeDef.matcher(url, init));
        if (!route) {
            throw new Error(`Unexpected fetch call to ${url}`);
        }
        return route.handler(url, init);
    });
}

export async function flushPromises(): Promise<void> {
    await Promise.resolve();
    await Promise.resolve();
}

export function waitForStateChanges(): Promise<void> {
    return new Promise((resolve) => queueMicrotask(resolve));
}
