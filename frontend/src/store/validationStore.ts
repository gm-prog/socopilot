import { create } from "zustand";

import type { ValidationReport } from "../lib/validation/reportValidationError";

export interface ValidationErrorEntry extends ValidationReport {
  id: string;
  timestamp: string;
}

interface ValidationStoreState {
  errors: ValidationErrorEntry[];
  droppedPacketCount: number;
  pushError: (entry: ValidationErrorEntry) => void;
  incrementDroppedPackets: (count?: number) => void;
  clearErrors: () => void;
}

export const useValidationStore = create<ValidationStoreState>((set) => ({
  errors: [],
  droppedPacketCount: 0,

  pushError: (entry) =>
    set((state) => ({
      errors: [entry, ...state.errors].slice(0, 25),
    })),

  incrementDroppedPackets: (count = 1) =>
    set((state) => ({
      droppedPacketCount: state.droppedPacketCount + count,
    })),

  clearErrors: () => set({ errors: [], droppedPacketCount: 0 }),
}));
