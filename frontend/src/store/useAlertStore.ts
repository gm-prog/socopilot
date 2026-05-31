import { create } from "zustand";
import type { AlertSummary } from "../types/alert";

interface AlertStore {
    alerts: AlertSummary[];

    setAlerts: (alerts: AlertSummary[]) => void;

    addAlert: (alert: AlertSummary, maxQueueSize?: number) => void;

    clearAlerts: () => void;
}

export const useAlertStore = create<AlertStore>((set) => ({
    alerts: [],

    setAlerts: (alerts) =>
        set({
            alerts,
        }),

    addAlert: (alert, maxQueueSize = 250) =>
        set((state) => {
            const filtered = state.alerts.filter(
                (item) => item.id !== alert.id
            );

            return {
                alerts: [alert, ...filtered].slice(0, maxQueueSize),
            };
        }),

    clearAlerts: () =>
        set({
            alerts: [],
        }),
}));