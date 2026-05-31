import { create } from "zustand";

import {
  fetchAlert,
  fetchAlertEnrichment,
  updateAlertWorkflow,
} from "../api/alerts";
import type {
  AlertDetail,
  AlertSummary,
  EnrichmentResult,
} from "../types/alert";

import type { Severity } from "./types";

export type FeedStatus = "NOMINAL" | "WARNING" | "CRITICAL";
export type ActiveRail = "ALL_STATIONS" | "CRITICAL_ONLY" | "NOMINAL_ONLY";

export interface FeedItem {
  id: string;
  type: string;
  origin: string;
  message: string;
  delta: string;
  status: FeedStatus;
  timestamp: string;
}

export interface ActiveFilters {
  sevFilter: "ALL" | Severity;
  stateFilter: string;
  searchQuery: string;
  activeRail: ActiveRail;
}

export interface AlertStoreState {
  alerts: AlertSummary[];

  selectedAlertId: string | null;
  selectedEntity: FeedItem | null;
  selectedRows: Set<string>;

  sevFilter: "ALL" | Severity;
  stateFilter: string;
  searchQuery: string;
  activeRail: ActiveRail;

  sortKey: "severity" | "id" | "entity" | "detected";
  sortDir: 1 | -1;

  alertDetail: AlertDetail | null;
  alertDetailEnrichment: EnrichmentResult[];
  detailLoading: boolean;
  detailError: string | null;
  drawerTab: "normalized" | "raw" | "timeline";
  drawerNotes: string;

  setAlerts: (alerts: AlertSummary[]) => void;
  addAlert: (alert: AlertSummary, maxQueueSize?: number) => void;
  clearAlerts: () => void;

  setSelectedAlertId: (id: string | null) => void;
  setSelectedEntity: (entity: FeedItem | null) => void;
  clearSelectedEntity: () => void;
  toggleSelectedRow: (id: string) => void;
  setSelectedRows: (rows: Set<string>) => void;
  clearSelectedRows: () => void;

  setSevFilter: (filter: "ALL" | Severity) => void;
  setStateFilter: (filter: string) => void;
  setSearchQuery: (query: string) => void;
  setActiveRail: (rail: ActiveRail) => void;
  setActiveFilters: (filters: Partial<ActiveFilters>) => void;
  resetFilters: () => void;

  setSortKey: (key: "severity" | "id" | "entity" | "detected") => void;
  setSortDir: (dir: 1 | -1) => void;

  setDrawerTab: (tab: "normalized" | "raw" | "timeline") => void;
  setDrawerNotes: (notes: string) => void;
  loadAlertDetail: (id: string) => Promise<void>;
  clearAlertDetail: () => void;
  updateAlertLifecycle: (state: string) => Promise<void>;
  saveDrawerNotes: () => Promise<void>;
  closeDetailDrawer: () => void;
}

const DEFAULT_FILTERS: ActiveFilters = {
  sevFilter: "ALL",
  stateFilter: "",
  searchQuery: "",
  activeRail: "ALL_STATIONS",
};

export const selectActiveFilters = (state: AlertStoreState): ActiveFilters => ({
  sevFilter: state.sevFilter,
  stateFilter: state.stateFilter,
  searchQuery: state.searchQuery,
  activeRail: state.activeRail,
});

export const useAlertStore = create<AlertStoreState>((set, get) => ({
  alerts: [],

  selectedAlertId: null,
  selectedEntity: null,
  selectedRows: new Set(),

  ...DEFAULT_FILTERS,

  sortKey: "detected",
  sortDir: -1,

  alertDetail: null,
  alertDetailEnrichment: [],
  detailLoading: false,
  detailError: null,
  drawerTab: "normalized",
  drawerNotes: "",

  setAlerts: (alerts) => set({ alerts }),

  addAlert: (alert, maxQueueSize = 250) =>
    set((state) => {
      const filtered = state.alerts.filter((item) => item.id !== alert.id);
      return {
        alerts: [alert, ...filtered].slice(0, maxQueueSize),
      };
    }),

  clearAlerts: () => set({ alerts: [] }),

  setSelectedAlertId: (id) => set({ selectedAlertId: id }),

  setSelectedEntity: (entity) => set({ selectedEntity: entity }),

  clearSelectedEntity: () => set({ selectedEntity: null }),

  toggleSelectedRow: (id) =>
    set((state) => {
      const newRows = new Set(state.selectedRows);
      if (newRows.has(id)) {
        newRows.delete(id);
      } else {
        newRows.add(id);
      }
      return { selectedRows: newRows };
    }),

  setSelectedRows: (rows) => set({ selectedRows: rows }),

  clearSelectedRows: () => set({ selectedRows: new Set() }),

  setSevFilter: (filter) => set({ sevFilter: filter }),

  setStateFilter: (filter) => set({ stateFilter: filter }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  setActiveRail: (rail) => set({ activeRail: rail }),

  setActiveFilters: (filters) =>
    set((state) => ({
      sevFilter: filters.sevFilter ?? state.sevFilter,
      stateFilter: filters.stateFilter ?? state.stateFilter,
      searchQuery: filters.searchQuery ?? state.searchQuery,
      activeRail: filters.activeRail ?? state.activeRail,
    })),

  resetFilters: () => set({ ...DEFAULT_FILTERS }),

  setSortKey: (key) => set({ sortKey: key }),

  setSortDir: (dir) => set({ sortDir: dir }),

  setDrawerTab: (tab) => set({ drawerTab: tab }),

  setDrawerNotes: (notes) => set({ drawerNotes: notes }),

  loadAlertDetail: async (id) => {
    set({ detailLoading: true, detailError: null });
    try {
      const [alert, enrichment] = await Promise.all([
        fetchAlert(id),
        fetchAlertEnrichment(id),
      ]);
      set({
        alertDetail: alert,
        alertDetailEnrichment: enrichment,
        drawerNotes: alert.analyst_notes || "",
        detailLoading: false,
      });
    } catch (err) {
      set({
        detailError: err instanceof Error ? err.message : "Error",
        detailLoading: false,
      });
    }
  },

  clearAlertDetail: () =>
    set({
      alertDetail: null,
      alertDetailEnrichment: [],
      detailLoading: false,
      detailError: null,
      drawerTab: "normalized",
      drawerNotes: "",
    }),

  updateAlertLifecycle: async (lifecycleState) => {
    const { selectedAlertId } = get();
    if (!selectedAlertId) return;

    const updated = await updateAlertWorkflow(selectedAlertId, {
      lifecycle_state: lifecycleState,
    });
    set({ alertDetail: updated });
  },

  saveDrawerNotes: async () => {
    const { selectedAlertId, drawerNotes } = get();
    if (!selectedAlertId) return;

    const updated = await updateAlertWorkflow(selectedAlertId, {
      analyst_notes: drawerNotes,
    });
    set({ alertDetail: updated });
  },

  closeDetailDrawer: () => {
    get().clearAlertDetail();
    set({ selectedAlertId: null });
  },
}));
