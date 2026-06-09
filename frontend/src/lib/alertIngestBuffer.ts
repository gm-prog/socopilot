import type { AlertSummary } from "../types/alert";

export interface AlertIngestBufferOptions {
  flushIntervalMs?: number;
  maxQueueSize?: number;
  onFlush: (alerts: AlertSummary[], maxQueueSize: number) => void;
}

/**
 * Batches high-frequency WebSocket alert events before committing to Zustand.
 * Prevents render jank under burst telemetry load.
 */
export class AlertIngestBuffer {
  private readonly queue = new Map<string, AlertSummary>();
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private rafId: number | null = null;
  private readonly flushIntervalMs: number;
  private readonly maxQueueSize: number;
  private readonly onFlush: AlertIngestBufferOptions["onFlush"];

  constructor(options: AlertIngestBufferOptions) {
    this.flushIntervalMs = options.flushIntervalMs ?? 200;
    this.maxQueueSize = options.maxQueueSize ?? 250;
    this.onFlush = options.onFlush;
  }

  start(): void {
    if (this.flushTimer !== null) return;
    this.flushTimer = setInterval(() => this.scheduleFlush(), this.flushIntervalMs);
  }

  enqueue(alert: AlertSummary): void {
    this.queue.set(alert.id, alert);
  }

  /** Coalesce flushes to one animation frame when possible */
  private scheduleFlush(): void {
    if (this.queue.size === 0) return;

    if (typeof requestAnimationFrame === "function") {
      if (this.rafId !== null) return;
      this.rafId = requestAnimationFrame(() => {
        this.rafId = null;
        this.flush();
      });
      return;
    }

    this.flush();
  }

  flush(): void {
    if (this.queue.size === 0) return;

    const batch = Array.from(this.queue.values());
    this.queue.clear();
    this.onFlush(batch, this.maxQueueSize);
  }

  dispose(): void {
    if (this.flushTimer !== null) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.flush();
  }
}
