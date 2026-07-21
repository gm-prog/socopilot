import { create } from "zustand";

export type NotificationLevel = "error" | "warning" | "info";

export interface AppNotification {
  id: string;
  level: NotificationLevel;
  message: string;
  timestamp: string;
}

interface NotificationStoreState {
  notifications: AppNotification[];
  push: (level: NotificationLevel, message: string) => void;
  pushError: (message: string) => void;
  pushWarning: (message: string) => void;
  dismiss: (id: string) => void;
  clear: () => void;
}

const MAX_NOTIFICATIONS = 10;

export const useNotificationStore = create<NotificationStoreState>((set) => ({
  notifications: [],

  push: (level, message) =>
    set((state) => ({
      notifications: [
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          level,
          message,
          timestamp: new Date().toISOString(),
        },
        ...state.notifications,
      ].slice(0, MAX_NOTIFICATIONS),
    })),

  pushError: (message) =>
    set((state) => ({
      notifications: [
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          level: "error",
          message,
          timestamp: new Date().toISOString(),
        },
        ...state.notifications,
      ].slice(0, MAX_NOTIFICATIONS),
    })),

  pushWarning: (message) =>
    set((state) => ({
      notifications: [
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          level: "warning",
          message,
          timestamp: new Date().toISOString(),
        },
        ...state.notifications,
      ].slice(0, MAX_NOTIFICATIONS),
    })),

  dismiss: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  clear: () => set({ notifications: [] }),
}));
