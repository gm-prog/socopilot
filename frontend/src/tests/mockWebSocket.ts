type EventListenerMap = Record<string, Set<EventListenerOrEventListenerObject>>;

export class MockWebSocket {
    public url: string;
    public readyState: number = MockWebSocket.CONNECTING;
    public onopen: ((event: Event) => void) | null = null;
    public onmessage: ((event: MessageEvent) => void) | null = null;
    public onclose: ((event: CloseEvent) => void) | null = null;
    public onerror: ((event: Event) => void) | null = null;
    public extensions = "";
    public protocol = "";
    public binaryType: BinaryType = "blob";
    public bufferedAmount = 0;

    private listeners: EventListenerMap = {};
    private server: MockWebSocketServer;

    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;

    constructor(server: MockWebSocketServer, url: string) {
        this.server = server;
        this.url = url;
        this.server.registerClient(this);
    }

    addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
        this.listeners[type] = this.listeners[type] || new Set();
        this.listeners[type].add(listener);
    }

    removeEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
        this.listeners[type]?.delete(listener);
    }

    dispatchEvent(event: Event): boolean {
        const handler = (this as any)[`on${event.type}`];
        if (typeof handler === "function") {
            handler.call(this, event);
        }
        const listeners = this.listeners[event.type];
        if (listeners) {
            listeners.forEach((listener) => {
                if (typeof listener === "function") {
                    listener.call(this, event);
                } else if (listener && typeof listener.handleEvent === "function") {
                    listener.handleEvent(event);
                }
            });
        }
        return true;
    }

    send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void {
        if (this.readyState !== MockWebSocket.OPEN) {
            throw new Error("WebSocket is not open");
        }
        this.server.receiveFromClient(this, data);
    }

    close(code = 1000, reason = ""): void {
        if (this.readyState === MockWebSocket.CLOSING || this.readyState === MockWebSocket.CLOSED) {
            return;
        }
        this.readyState = MockWebSocket.CLOSING;
        this.server.closeClient(this, code, reason);
    }

    triggerOpen(): void {
        if (this.readyState !== MockWebSocket.CONNECTING) return;
        this.readyState = MockWebSocket.OPEN;
        this.dispatchEvent(new Event("open"));
    }

    triggerMessage(data: unknown): void {
        if (this.readyState !== MockWebSocket.OPEN) return;
        this.dispatchEvent(new MessageEvent("message", { data }));
    }

    triggerError(): void {
        this.dispatchEvent(new Event("error"));
    }

    triggerClose(code = 1000, reason = ""): void {
        if (this.readyState === MockWebSocket.CLOSED) return;
        this.readyState = MockWebSocket.CLOSED;
        this.dispatchEvent(new CloseEvent("close", { code, reason, wasClean: code === 1000 }));
    }
}

export class MockWebSocketServer {
    public clients = new Set<MockWebSocket>();
    public connectionCount = 0;
    public lastCreated: MockWebSocket | null = null;

    registerClient(client: MockWebSocket): void {
        this.clients.add(client);
        this.lastCreated = client;
        this.connectionCount += 1;
        queueMicrotask(() => {
            if (this.clients.has(client)) {
                client.triggerOpen();
            }
        });
    }

    connect(url: string): MockWebSocket {
        return new MockWebSocket(this, url);
    }

    closeClient(client: MockWebSocket, code = 1000, reason = ""): void {
        if (!this.clients.has(client)) return;
        this.clients.delete(client);
        client.triggerClose(code, reason);
    }

    disconnectAll(code = 1000, reason = ""): void {
        for (const client of Array.from(this.clients)) {
            this.closeClient(client, code, reason);
        }
    }

    broadcast(data: unknown): void {
        for (const client of [...this.clients]) {
            client.triggerMessage(data);
        }
    }

    receiveFromClient(client: MockWebSocket, data: unknown): void {
        // intentionally left as a hook for tests that need request inspection
    }

    get activeConnections(): number {
        return this.clients.size;
    }
}

export function installMockWebSocket(server: MockWebSocketServer): void {
    const MockWebSocketConstructor = class {
        constructor(url: string) {
            return server.connect(url) as unknown as WebSocket;
        }
    };

    (globalThis as any).WebSocket = MockWebSocketConstructor as unknown as typeof WebSocket;
}
