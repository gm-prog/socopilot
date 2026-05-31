import { useState, useEffect, useRef, useCallback } from "react";

import { useAuth } from "../context/AuthContext";
import { fetchAlerts } from "../api/alerts";
import { websocketUrl } from "../config/api";
import { WebSocketManager } from "../lib/websocketManager";

import { useAlertStore } from "../store/alertStore";

import type { AlertSummary } from "../types/alert";

interface UseAlertsStreamOptions {
    maxQueueSize?: number;
    enabled?: boolean;
}

export const useAlertsStream = ({
    maxQueueSize = 250,
    enabled = true,
}: UseAlertsStreamOptions = {}) => {
    const { token, isAuthenticated, refreshSession, logout } = useAuth();

    const [isConnected, setIsConnected] = useState(false);

    const [error, setError] = useState<string | null>(null);

    const [isLoading, setIsLoading] = useState(true);

    const [reconnectAttempts, setReconnectAttempts] = useState(0);

    const [activeSocketCount, setActiveSocketCount] = useState(0);

    const managerRef = useRef<WebSocketManager | null>(null);

    /**
     * Zustand store actions
     */
    const setAlerts = useAlertStore((state) => state.setAlerts);

    const addAlert = useAlertStore((state) => state.addAlert);

    const fetchHistoricalAlerts = useCallback(async () => {
        if (!isAuthenticated || !token) {
            return;
        }

        try {
            setIsLoading(true);

            const response = await fetchAlerts({
                page_size: maxQueueSize,
            });

            setAlerts(response.items || []);

            setError(null);
        } catch (err: any) {
            setError(
                `Initial alert fetch failed: ${err.message}`
            );

            setAlerts([]);
        } finally {
            setIsLoading(false);
        }
    }, [
        isAuthenticated,
        token,
        maxQueueSize,
        setAlerts,
    ]);

    const parseWebSocketFrame = useCallback(
        (raw: string): AlertSummary | null => {
            try {
                const data = JSON.parse(raw);

                if (data.type === "NEW_ALERT" && data.data) {
                    return data.data as AlertSummary;
                }

                if (data.id && data.title) {
                    return data as AlertSummary;
                }

                return null;
            } catch {
                return null;
            }
        },
        []
    );

    useEffect(() => {
        if (!enabled) {
            return;
        }

        const manager = new WebSocketManager({
            getUrl: () =>
                websocketUrl("/ws/alerts", {
                    token,
                }),

            getToken: () => token,

            createWebSocket: (url) =>
                new WebSocket(url),

            onOpen: () => {
                setIsConnected(true);

                setError(null);

                setActiveSocketCount(1);

                setReconnectAttempts(0);
            },

            onMessage: (event) => {
                const incomingData =
                    parseWebSocketFrame(event.data);

                if (!incomingData) {
                    return;
                }

                addAlert(
                    incomingData,
                    maxQueueSize
                );
            },

            onError: () => {
                setIsConnected(false);

                setError(
                    "Alert stream connection error. Attempting reconnect..."
                );
            },

            onClose: () => {
                setIsConnected(false);

                setActiveSocketCount(0);
            },

            onReconnectAttempt: (
                attempt,
                delayMs
            ) => {
                setReconnectAttempts(attempt);

                setError(
                    `Reconnect attempt ${attempt} in ${delayMs}ms`
                );
            },

            onAuthFailure: async () => {
                const refreshed =
                    await refreshSession();

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
        parseWebSocketFrame,
        addAlert,
        maxQueueSize,
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