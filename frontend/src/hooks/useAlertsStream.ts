import { useEffect, useMemo, useSyncExternalStore } from "react";

import { useAuth } from "../context/AuthContext";
import { fetchAlerts } from "../api/alerts";
import { websocketUrl } from "../config/api";
import { WebSocketManager } from "../lib/websocketManager";
import { AlertIngestBuffer } from "../lib/alertIngestBuffer";
import { parseWebSocketAlertFrame } from "../lib/validation/parseWebSocketAlert";

import { useAlertStore } from "../store/alertStore";

interface UseAlertsStreamOptions {
  maxQueueSize?: number;
  enabled?: boolean;
  /** Batch flush interval in ms (default 200) */
  flushIntervalMs?: number;
}

interface StreamState {
  isConnected: boolean;
  error: string | null;
  isLoading: boolean;
  reconnectAttempts: number;
  activeSocketCount: number;
}

interface StreamConsumerConfig {
  enabled: boolean;
  maxQueueSize: number;
  flushIntervalMs: number;
  token: string | null;
  isAuthenticated: boolean;
  refreshSession: () => Promise<boolean>;
  logout: () => Promise<void> | void;
  setAlerts: (alerts: unknown[]) => void;
  addAlertsBatch: (batch: unknown[], queueCap: number) => void;
}

type StreamListener = () => void;

class AlertsStreamController {
  private listeners = new Set<StreamListener>();
  private state: StreamState = {
    isConnected: false,
    error: null,
    isLoading: true,
    reconnectAttempts: 0,
    activeSocketCount: 0,
  };

  private manager: WebSocketManager | null = null;
  private buffer: AlertIngestBuffer | null = null;
  private currentConfig: StreamConsumerConfig | null = null;
  private activeConsumers = new Map<number, StreamConsumerConfig>();
  private nextConsumerId = 0;
  private fetchInFlight: Promise<void> | null = null;

  subscribe(listener: StreamListener) {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  getSnapshot() {
    return this.state;
  }

  registerConsumer(config: StreamConsumerConfig) {
    const consumerId = this.nextConsumerId + 1;
    this.nextConsumerId = consumerId;
    this.activeConsumers.set(consumerId, config);
    this.sync();

    return () => {
      this.activeConsumers.delete(consumerId);
      this.sync();
    };
  }

  refreshHistoricalAlerts() {
    void this.fetchHistoricalAlerts();
  }

  private sync() {
    const config = this.getEffectiveConfig();

    if (!config || !config.enabled || !config.isAuthenticated || !config.token) {
      this.teardown();
      return;
    }

    if (this.currentConfig && this.isSameConfig(this.currentConfig, config)) {
      this.fetchHistoricalAlerts();
      return;
    }

    this.teardown();
    this.currentConfig = config;
    this.startStream(config);
    void this.fetchHistoricalAlerts();
  }

  private getEffectiveConfig() {
    const consumers = Array.from(this.activeConsumers.values());
    if (consumers.length === 0) {
      return null;
    }

    return (
      consumers.find(
        (consumer) => consumer.enabled && consumer.isAuthenticated && Boolean(consumer.token)
      ) ?? consumers[consumers.length - 1] ?? null
    );
  }

  private isSameConfig(a: StreamConsumerConfig, b: StreamConsumerConfig) {
    return (
      a.enabled === b.enabled &&
      a.maxQueueSize === b.maxQueueSize &&
      a.flushIntervalMs === b.flushIntervalMs &&
      a.token === b.token &&
      a.isAuthenticated === b.isAuthenticated
    );
  }

  private async fetchHistoricalAlerts() {
    const config = this.currentConfig ?? this.getEffectiveConfig();
    if (!config || !config.isAuthenticated || !config.token) {
      return;
    }

    if (this.fetchInFlight) {
      return this.fetchInFlight;
    }

    this.updateState({ isLoading: true, error: null });
    this.fetchInFlight = (async () => {
      try {
        const response = await fetchAlerts({
          page_size: config.maxQueueSize,
        });

        config.setAlerts(response.items);
        this.updateState({ error: null, isLoading: false });
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Initial alert fetch failed";
        config.setAlerts([]);
        this.updateState({
          error: `Initial alert fetch failed: ${message}`,
          isLoading: false,
        });
      } finally {
        this.fetchInFlight = null;
      }
    })();

    return this.fetchInFlight;
  }

  private startStream(config: StreamConsumerConfig) {
    const buffer = new AlertIngestBuffer({
      flushIntervalMs: config.flushIntervalMs,
      maxQueueSize: config.maxQueueSize,
      onFlush: (batch, queueCap) => {
        config.addAlertsBatch(batch, queueCap);
      },
    });
    buffer.start();
    this.buffer = buffer;

    const manager = new WebSocketManager({
      getUrl: () =>
        websocketUrl("/ws/alerts", {
          token: config.token ?? "",
        }),
      getToken: () => config.token,
      createWebSocket: (url) => new WebSocket(url),
      onOpen: () => {
        this.updateState({
          isConnected: true,
          error: null,
          reconnectAttempts: 0,
          activeSocketCount: 1,
        });
      },
      onMessage: (event) => {
        const incomingData = parseWebSocketAlertFrame(event.data);
        if (!incomingData) {
          return;
        }
        buffer.enqueue(incomingData);
      },
      onError: () => {
        this.updateState({
          isConnected: false,
          error: "Alert stream connection error. Attempting reconnect...",
        });
      },
      onClose: () => {
        this.updateState({ isConnected: false, activeSocketCount: 0 });
      },
      onReconnectAttempt: (attempt, delayMs) => {
        this.updateState({
          reconnectAttempts: attempt,
          error: `Reconnect attempt ${attempt} in ${delayMs}ms`,
        });
      },
      onAuthFailure: async () => {
        const refreshed = await config.refreshSession();
        if (!refreshed) {
          await config.logout();
          return false;
        }
        return true;
      },
      initialBackoffMs: 500,
      maxBackoffMs: 25000,
      jitterMs: 100,
      maxReconnectAttempts: 8,
    });

    this.manager = manager;
    manager.start();
  }

  private teardown() {
    this.buffer?.dispose();
    this.buffer = null;
    this.manager?.dispose();
    this.manager = null;
    this.currentConfig = null;
    this.updateState({ isConnected: false, activeSocketCount: 0 });
  }

  private updateState(patch: Partial<StreamState>) {
    this.state = {
      ...this.state,
      ...patch,
    };
    this.listeners.forEach((listener) => listener());
  }
}

const alertsStreamController = new AlertsStreamController();

export const useAlertsStream = (options: UseAlertsStreamOptions = {}) => {
  const normalizedOptions = useMemo(
    () => ({
      maxQueueSize: options.maxQueueSize ?? 250,
      enabled: options.enabled ?? true,
      flushIntervalMs: options.flushIntervalMs ?? 200,
    }),
    [options.maxQueueSize, options.enabled, options.flushIntervalMs]
  );

  const { token, isAuthenticated, refreshSession, logout } = useAuth();
  const setAlerts = useAlertStore((state) => state.setAlerts);
  const addAlertsBatch = useAlertStore((state) => state.addAlertsBatch);

  const streamState = useSyncExternalStore(
    alertsStreamController.subscribe.bind(alertsStreamController),
    alertsStreamController.getSnapshot.bind(alertsStreamController),
    alertsStreamController.getSnapshot.bind(alertsStreamController)
  );

  useEffect(() => {
    const unsubscribe = alertsStreamController.registerConsumer({
      enabled: normalizedOptions.enabled,
      maxQueueSize: normalizedOptions.maxQueueSize,
      flushIntervalMs: normalizedOptions.flushIntervalMs,
      token,
      isAuthenticated,
      refreshSession,
      logout,
      setAlerts,
      addAlertsBatch,
    });

    return unsubscribe;
  }, [
    normalizedOptions.enabled,
    normalizedOptions.maxQueueSize,
    normalizedOptions.flushIntervalMs,
    token,
    isAuthenticated,
    refreshSession,
    logout,
    setAlerts,
    addAlertsBatch,
  ]);

  return {
    isConnected: streamState.isConnected,
    error: streamState.error,
    isLoading: streamState.isLoading,
    reconnectAttempts: streamState.reconnectAttempts,
    activeSocketCount: streamState.activeSocketCount,
    refetch: () => alertsStreamController.refreshHistoricalAlerts(),
  };
};
