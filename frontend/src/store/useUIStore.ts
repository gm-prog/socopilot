import { create } from 'zustand';

interface UIStore {
  copilotOpen: boolean;
  setCopilotOpen: (open: boolean) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  copilotOpen: false,
  setCopilotOpen: (open) => set({ copilotOpen: open }),
}));
