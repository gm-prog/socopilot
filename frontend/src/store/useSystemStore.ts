import { create } from 'zustand';

interface SystemState {
    // Metrics
    eventRate: number;
    pipelineHealth: number;
    openAlertsCount: number;
    criticalAlertsCount: number;

    // System status
    isHealthy: boolean;
    isReady: boolean;

    // Actions
    setEventRate: (rate: number) => void;
    setPipelineHealth: (health: number) => void;
    setOpenAlertsCount: (count: number) => void;
    setCriticalAlertsCount: (count: number) => void;
    setIsHealthy: (healthy: boolean) => void;
    setIsReady: (ready: boolean) => void;

    // Batch update
    updateMetrics: (updates: Partial<Omit<SystemState, keyof SystemActions>>) => void;
}

interface SystemActions {
    setEventRate: (rate: number) => void;
    setPipelineHealth: (health: number) => void;
    setOpenAlertsCount: (count: number) => void;
    setCriticalAlertsCount: (count: number) => void;
    setIsHealthy: (healthy: boolean) => void;
    setIsReady: (ready: boolean) => void;
    updateMetrics: (updates: Partial<Omit<SystemState, keyof SystemActions>>) => void;
}

export const useSystemStore = create<SystemState>((set) => ({
    eventRate: 0,
    pipelineHealth: 99.8,
    openAlertsCount: 0,
    criticalAlertsCount: 0,
    isHealthy: true,
    isReady: false,

    setEventRate: (rate) => set({ eventRate: rate }),

    setPipelineHealth: (health) => set({ pipelineHealth: health }),

    setOpenAlertsCount: (count) => set({ openAlertsCount: count }),

    setCriticalAlertsCount: (count) => set({ criticalAlertsCount: count }),

    setIsHealthy: (healthy) => set({ isHealthy: healthy }),

    setIsReady: (ready) => set({ isReady: ready }),

    updateMetrics: (updates) => set(updates),
}));
