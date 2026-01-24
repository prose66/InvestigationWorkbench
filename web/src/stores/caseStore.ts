import { create } from "zustand";
import { persist } from "zustand/middleware";

interface CaseState {
  // Current selected case
  selectedCaseId: string | null;

  // Recent entities (for quick access)
  recentEntities: Array<{ type: string; value: string }>;

  // Actions
  setSelectedCaseId: (caseId: string | null) => void;
  addRecentEntity: (type: string, value: string) => void;
  clearRecentEntities: () => void;
}

export const useCaseStore = create<CaseState>()(
  persist(
    (set, get) => ({
      selectedCaseId: null,
      recentEntities: [],

      setSelectedCaseId: (caseId) => {
        const current = get().selectedCaseId;
        if (current !== caseId) {
          // Clear recent entities when switching cases
          set({ selectedCaseId: caseId, recentEntities: [] });
        } else {
          set({ selectedCaseId: caseId });
        }
      },

      addRecentEntity: (type, value) => {
        const { recentEntities } = get();
        const newEntity = { type, value };
        // Remove duplicates and add to front
        const filtered = recentEntities.filter(
          (e) => !(e.type === type && e.value === value)
        );
        set({ recentEntities: [newEntity, ...filtered].slice(0, 10) });
      },

      clearRecentEntities: () => {
        set({ recentEntities: [] });
      },
    }),
    {
      name: "case-storage",
    }
  )
);
