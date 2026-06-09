import { useState, useEffect, useRef, useCallback } from "react";

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

export const useAlertsStream = ({
  maxQueueSize = 250,
  enabled = true,
  flushIntervalMs = 200,
}: UseAlertsStreamOptions = {}) => {
  const { token, isAuthenticated, refreshSession, logout } = useAuth();

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [activeSocketCount, setActiveSocketCount] = useState(0);

  const managerRef = useRef<WebSocketManager | null>(null);
  const bufferRef = useRef<AlertIngestBuffer | null>(null);

  const setAlerts = useAlertStore((state) => state.setAlerts);
  const addAlertsBatch = useAlertStore((state) => state.addAlertsBatch);

  const fetchHistoricalAlerts = useCallback(async () => {
    if (!isAuthenticated || !token) {
      return;
    }

    try {
      setIsLoading(true);

      const response = await fetchAlerts({
        page_size: maxQueueSize,
      });

      setAlerts(response.items);

      setError(null);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Initial alert fetch failed";
      setError(`Initial alert fetch failed: ${message}`);
      setAlerts([]);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, token, maxQueueSize, setAlerts]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const buffer = new AlertIngestBuffer({
      flushIntervalMs,
      maxQueueSize,
      onFlush: (batch, queueCap) => {
        addAlertsBatch(batch, queueCap);
      },
    });
    buffer.start();
    bufferRef.current = buffer;

    const manager = new WebSocketManager({
      getUrl: () =>
        websocketUrl("/ws/alerts", {
          token,
        }),

      getToken: () => token,

      createWebSocket: (url) => new WebSocket(url),

      onOpen: () => {
        setIsConnected(true);
        setError(null);
        setActiveSocketCount(1);
        setReconnectAttempts(0);
      },

      onMessage: (event) => {
        const incomingData = parseWebSocketAlertFrame(event.data);
        if (!incomingData) {
          return;
        }
        buffer.enqueue(incomingData);
      },

      onError: () => {
        setIsConnected(false);
        setError("Alert stream connection error. Attempting reconnect...");
      },

      onClose: () => {
        setIsConnected(false);
        setActiveSocketCount(0);
      },

      onReconnectAttempt: (attempt, delayMs) => {
        setReconnectAttempts(attempt);
        setError(`Reconnect attempt ${attempt} in ${delayMs}ms`);
      },

      onAuthFailure: async () => {
        const refreshed = await refreshSession();
        if (!refreshed) {
          await logout();
          return false;
        }
        return true;
      },

      initialBackoffMs: 500,
      maxBackoffMs: 25000,
      jitterMs: 100,
      maxReconnectAttempts: 8,
    });

    managerRef.current = manager;

    if (isAuthenticated && token) {
      fetchHistoricalAlerts();
      manager.start();
    }

    return () => {
      buffer.dispose();
      bufferRef.current = null;
      manager.dispose();
      managerRef.current = null;
    };
  }, [
    enabled,
    token,
    isAuthenticated,
    refreshSession,
    logout,
    fetchHistoricalAlerts,
    addAlertsBatch,
    maxQueueSize,
    flushIntervalMs,
  ]);

  return {
    isConnected,
    error,
    isLoading,
    reconnectAttempts,
    activeSocketCount,
    refetch: fetchHistoricalAlerts,
  };
};
