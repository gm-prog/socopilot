export interface WebSocketManagerOptions {
    getUrl: () => string;
    getToken: () => string | null;
    createWebSocket: (url: string) => WebSocket;
    onOpen?: () => void;
    onMessage?: (event: MessageEvent) => void;
    onClose?: (event: CloseEvent) => void;
    onError?: (event: Event) => void;
    onReconnectAttempt?: (attempt: number, delayMs: number) => void;
    onAuthFailure?: () => Promise<boolean>;
    initialBackoffMs?: number;
    maxBackoffMs?: number;
    maxReconnectAttempts?: number;
    jitterMs?: number;
    logger?: (message: string) => void;
}

export interface WebSocketManagerState {
    activeSocketCount: number;
    reconnectAttempts: number;
    isRunning: boolean;
    hasPendingReconnect: boolean;
}

export class WebSocketManager {
    private socket: WebSocket | null = null;
    private reconnectTimer: number | null = null;
    private reconnectAttempts = 0;
    private closed = false;
    private connecting = false;

    constructor(private options: WebSocketManagerOptions) { }

    get state(): WebSocketManagerState {
        return {
            activeSocketCount: this.socket ? 1 : 0,
            reconnectAttempts: this.reconnectAttempts,
            isRunning: !!this.socket || !this.closed,
            hasPendingReconnect: this.reconnectTimer !== null,
        };
    }

    start(): void {
        if (this.closed) {
            this.closed = false;
        }
        this.debug("start requested");
        this.connect();
    }

    stop(): void {
        this.debug("stop requested");
        this.closed = true;
        this.clearReconnect();
        this.closeSocket(1000, "Stopped");
    }

    dispose(): void {
        this.stop();
    }

    private debug(message: string): void {
        this.options.logger?.(`[WebSocketManager] ${message}`);
    }

    private getDelayMs(): number {
        const initial = this.options.initialBackoffMs ?? 500;
        const maxDelay = this.options.maxBackoffMs ?? 25000;
        const base = Math.min(maxDelay, initial * 2 ** this.reconnectAttempts);
        const jitter = this.options.jitterMs ?? 200;
        return Math.min(maxDelay, base + Math.floor(Math.random() * jitter));
    }

    private connect(): void {
        if (this.closed) {
            this.debug("connect aborted because manager is closed");
            return;
        }
        if (this.socket || this.connecting) {
            this.debug("connect skipped because a socket already exists");
            return;
        }

        const token = this.options.getToken();
        if (!token) {
            this.debug("connect aborted because token is unavailable");
            return;
        }

        const url = this.options.getUrl();
        this.debug(`connecting to ${url}`);
        this.connecting = true;
        const socket = this.options.createWebSocket(url);
        this.socket = socket;

        socket.addEventListener("open", () => {
            this.connecting = false;
            this.reconnectAttempts = 0;
            this.clearReconnect();
            this.debug("socket opened");
            this.options.onOpen?.();
        });

        socket.addEventListener("message", (event) => {
            this.options.onMessage?.(event);
        });

        socket.addEventListener("error", (event) => {
            this.debug("socket reported error");
            this.options.onError?.(event);
            socket.close();
        });

        socket.addEventListener("close", async (event) => {
            this.debug(`socket closed code=${event.code}`);
            this.options.onClose?.(event);
            this.socket = null;
            this.connecting = false;

            if (this.closed || event.code === 1000) {
                this.debug("socket close will not reconnect");
                return;
            }

            if (event.code === 1008 && this.options.onAuthFailure) {
                this.debug("authentication failure detected on socket close");
                const refreshed = await this.options.onAuthFailure();
                if (!refreshed) {
                    this.debug("authentication failure handler declined reconnect");
                    this.stop();
                    return;
                }
            }

            if (this.options.maxReconnectAttempts !== undefined && this.reconnectAttempts >= this.options.maxReconnectAttempts) {
                this.debug("reconnect limit reached");
                return;
            }

            const delayMs = this.getDelayMs();
            this.reconnectAttempts += 1;
            this.options.onReconnectAttempt?.(this.reconnectAttempts, delayMs);
            this.debug(`scheduling reconnect attempt=${this.reconnectAttempts} delay=${delayMs}`);
            this.clearReconnect();
            this.reconnectTimer = window.setTimeout(() => {
                this.reconnectTimer = null;
                this.connect();
            }, delayMs) as unknown as number;
        });
    }

    private closeSocket(code: number, reason: string): void {
        if (!this.socket) return;
        const socket = this.socket;
        this.socket = null;
        try {
            socket.close(code, reason);
        } catch {
            // swallow close errors during teardown
        }
    }

    private clearReconnect(): void {
        if (this.reconnectTimer !== null) {
            window.clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }
}
