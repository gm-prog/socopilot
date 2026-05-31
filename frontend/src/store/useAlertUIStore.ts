import { create } from 'zustand';
import { Severity, AlertState } from './types';

interface AlertUIState {
  // Selection
  selectedAlertId: string | null;
  selectedRows: Set<string>;

  // Filters
  sevFilter: 'ALL' | Severity;
  stateFilter: string;
  searchQuery: string;

  // Sorting
  sortKey: 'severity' | 'id' | 'entity' | 'detected';
  sortDir: 1 | -1;

  // Actions
  setSelectedAlertId: (id: string | null) => void;
  toggleSelectedRow: (id: string) => void;
  setSelectedRows: (rows: Set<string>) => void;
  clearSelectedRows: () => void;

  setSevFilter: (filter: 'ALL' | Severity) => void;
  setStateFilter: (filter: string) => void;
  setSearchQuery: (query: string) => void;

  setSortKey: (key: 'severity' | 'id' | 'entity' | 'detected') => void;
  setSortDir: (dir: 1 | -1) => void;

  // Reset all filters
  resetFilters: () => void;
}

export const useAlertUIStore = create<AlertUIState>((set) => ({
  selectedAlertId: null,
  selectedRows: new Set(),
  sevFilter: 'ALL',
  stateFilter: '',
  searchQuery: '',
  sortKey: 'detected',
  sortDir: -1,

  setSelectedAlertId: (id) => set({ selectedAlertId: id }),

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

  setSortKey: (key) => set({ sortKey: key }),

  setSortDir: (dir) => set({ sortDir: dir }),

  resetFilters: () =>
    set({
      sevFilter: 'ALL',
      stateFilter: '',
      searchQuery: '',
      sortKey: 'detected',
      sortDir: -1,
    }),
}));
