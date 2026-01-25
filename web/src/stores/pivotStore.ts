import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PivotEntity } from "@/lib/types";

interface PivotState {
  // Current pivot entities (AND filter chain)
  pivotEntities: PivotEntity[];

  // Current case ID
  caseId: string | null;

  // Actions
  setCaseId: (caseId: string) => void;
  addPivotEntity: (entity: PivotEntity) => void;
  removePivotEntity: (index: number) => void;
  clearPivotEntities: () => void;
  setPivotEntitySingle: (entity: PivotEntity) => void;
  setPivotEntities: (entities: PivotEntity[]) => void;
}

// Map entity types to column names
export const ENTITY_COLUMN_MAP: Record<string, string> = {
  host: "host",
  user: "user",
  ip: "src_ip",
  hash: "file_hash",
  process: "process_name",
};

// Helper to create a pivot entity
export function createPivotEntity(type: string, value: string): PivotEntity {
  return {
    type,
    column: ENTITY_COLUMN_MAP[type] || type,
    value,
  };
}

// Serialize pivot entities to URL param format: "host:web01,user:admin"
export function serializePivots(entities: PivotEntity[]): string {
  if (entities.length === 0) return "";
  return entities.map((e) => `${e.type}:${encodeURIComponent(e.value)}`).join(",");
}

// Deserialize URL param to pivot entities
export function deserializePivots(param: string | null): PivotEntity[] {
  if (!param) return [];
  try {
    return param.split(",").map((part) => {
      const [type, encodedValue] = part.split(":");
      const value = decodeURIComponent(encodedValue || "");
      return createPivotEntity(type, value);
    });
  } catch {
    return [];
  }
}

export const usePivotStore = create<PivotState>()(
  persist(
    (set, get) => ({
      pivotEntities: [],
      caseId: null,

      setCaseId: (caseId) => {
        const current = get().caseId;
        if (current !== caseId) {
          // Clear pivots when switching cases
          set({ caseId, pivotEntities: [] });
        } else {
          set({ caseId });
        }
      },

      addPivotEntity: (entity) => {
        const { pivotEntities } = get();
        // Avoid duplicates
        const exists = pivotEntities.some(
          (e) => e.column === entity.column && e.value === entity.value
        );
        if (!exists) {
          set({ pivotEntities: [...pivotEntities, entity] });
        }
      },

      removePivotEntity: (index) => {
        const { pivotEntities } = get();
        set({
          pivotEntities: pivotEntities.filter((_, i) => i !== index),
        });
      },

      clearPivotEntities: () => {
        set({ pivotEntities: [] });
      },

      setPivotEntitySingle: (entity) => {
        set({ pivotEntities: [entity] });
      },

      setPivotEntities: (entities) => {
        set({ pivotEntities: entities });
      },
    }),
    {
      name: "pivot-storage",
    }
  )
);

// Helper to get filter params from pivot entities
export function getPivotFilterParams(
  pivotEntities: PivotEntity[]
): Record<string, string[]> {
  const params: Record<string, string[]> = {
    hosts: [],
    users: [],
    ips: [],
    processes: [],
    hashes: [],
  };

  for (const entity of pivotEntities) {
    switch (entity.column) {
      case "host":
        params.hosts.push(entity.value);
        break;
      case "user":
        params.users.push(entity.value);
        break;
      case "src_ip":
        params.ips.push(entity.value);
        break;
      case "process_name":
        params.processes.push(entity.value);
        break;
      case "file_hash":
        params.hashes.push(entity.value);
        break;
    }
  }

  return params;
}
