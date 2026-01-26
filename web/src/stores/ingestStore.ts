import { create } from "zustand";
import type {
  PreviewResponse,
  IngestResponse,
  FieldMapping,
  FileEntry,
} from "@/lib/types";

export type IngestStep = "files" | "schema" | "mapping" | "entities" | "confirm" | "ingesting" | "complete";

interface IngestState {
  // Current step
  step: IngestStep;

  // Multiple files
  files: FileEntry[];

  // Merged working schema (union of all source fields)
  workingSchema: string[];

  // Unified mappings (source_field -> unified_field)
  fieldMappings: Record<string, string | null>;

  // Track which file each source field comes from (for UI display)
  fieldSources: Record<string, string[]>; // field -> [fileId1, fileId2, ...]

  // Entity fields (from unified field names, not source)
  entityFields: string[];

  // Global settings
  saveMapper: boolean;
  timeStart: string;
  timeEnd: string;

  // Results (per file)
  results: Record<string, IngestResponse>; // fileId -> result
  isIngesting: boolean;
  ingestError: string | null;
  currentIngestIndex: number;

  // Actions - File management
  addFile: (file: File) => string; // returns fileId
  removeFile: (fileId: string) => void;
  updateFileSource: (fileId: string, source: string) => void;
  updateFileQueryName: (fileId: string, queryName: string) => void;
  setFilePreview: (fileId: string, preview: PreviewResponse) => void;
  setFileLoading: (fileId: string, loading: boolean) => void;
  setFileError: (fileId: string, error: string | null) => void;

  // Actions - Schema building
  buildMergedSchema: () => void;

  // Actions - Mappings
  updateMapping: (sourceField: string, unifiedField: string | null) => void;
  toggleEntityField: (field: string) => void;
  setSaveMapper: (save: boolean) => void;
  setTimeStart: (time: string) => void;
  setTimeEnd: (time: string) => void;

  // Actions - Results
  setResult: (fileId: string, result: IngestResponse) => void;
  setIngesting: (ingesting: boolean) => void;
  setIngestError: (error: string | null) => void;
  setCurrentIngestIndex: (index: number) => void;

  // Actions - Navigation
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: IngestStep) => void;
  reset: () => void;

  // Computed
  canProceed: () => boolean;
  getMappingsArray: () => FieldMapping[];
  getFilesWithPreviews: () => FileEntry[];
  getTotalRows: () => number;
  getTotalIngested: () => number;
  getTotalSkipped: () => number;
}

const STEP_ORDER: IngestStep[] = ["files", "schema", "mapping", "entities", "confirm", "ingesting", "complete"];

function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

const initialState = {
  step: "files" as IngestStep,
  files: [] as FileEntry[],
  workingSchema: [] as string[],
  fieldMappings: {} as Record<string, string | null>,
  fieldSources: {} as Record<string, string[]>,
  entityFields: [] as string[],
  saveMapper: false,
  timeStart: "",
  timeEnd: "",
  results: {} as Record<string, IngestResponse>,
  isIngesting: false,
  ingestError: null as string | null,
  currentIngestIndex: 0,
};

export const useIngestStore = create<IngestState>()((set, get) => ({
  ...initialState,

  // File management
  addFile: (file) => {
    const id = generateId();
    const newFile: FileEntry = {
      id,
      file,
      source: "",
      queryName: "",
      previewData: null,
      isLoading: false,
      error: null,
    };
    set((state) => ({ files: [...state.files, newFile] }));
    return id;
  },

  removeFile: (fileId) => {
    set((state) => ({
      files: state.files.filter((f) => f.id !== fileId),
    }));
    // Rebuild schema after file removal
    get().buildMergedSchema();
  },

  updateFileSource: (fileId, source) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === fileId ? { ...f, source } : f
      ),
    }));
  },

  updateFileQueryName: (fileId, queryName) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === fileId ? { ...f, queryName } : f
      ),
    }));
  },

  setFilePreview: (fileId, preview) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === fileId ? { ...f, previewData: preview, error: null } : f
      ),
    }));
  },

  setFileLoading: (fileId, loading) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === fileId ? { ...f, isLoading: loading } : f
      ),
    }));
  },

  setFileError: (fileId, error) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === fileId ? { ...f, error, isLoading: false } : f
      ),
    }));
  },

  // Schema building
  buildMergedSchema: () => {
    const { files } = get();
    const filesWithPreviews = files.filter((f) => f.previewData !== null);

    // Collect all unique fields and track which files have each field
    const fieldSourcesMap: Record<string, string[]> = {};
    const allMappings: Record<string, string> = {};

    for (const file of filesWithPreviews) {
      if (!file.previewData) continue;

      for (const field of file.previewData.source_fields) {
        if (!fieldSourcesMap[field]) {
          fieldSourcesMap[field] = [];
        }
        fieldSourcesMap[field].push(file.id);

        // Collect suggested mappings (first one wins)
        if (!allMappings[field] && file.previewData.suggested_mappings[field]) {
          allMappings[field] = file.previewData.suggested_mappings[field];
        }
      }
    }

    // Build working schema (unique fields)
    const workingSchema = Object.keys(fieldSourcesMap).sort();

    // Initialize field mappings from suggestions
    const fieldMappings: Record<string, string | null> = {};
    for (const field of workingSchema) {
      fieldMappings[field] = allMappings[field] || null;
    }

    // Auto-select common entity fields
    const entityFields: string[] = [];
    const entityPatterns = ["host", "user", "src_ip", "dest_ip", "file_hash", "process_name"];
    for (const [source, unified] of Object.entries(allMappings)) {
      if (entityPatterns.includes(unified)) {
        entityFields.push(source);
      }
    }

    set({
      workingSchema,
      fieldSources: fieldSourcesMap,
      fieldMappings,
      entityFields,
    });
  },

  // Mappings
  updateMapping: (sourceField, unifiedField) => {
    set((state) => ({
      fieldMappings: { ...state.fieldMappings, [sourceField]: unifiedField },
    }));
  },

  toggleEntityField: (field) => {
    set((state) => {
      if (state.entityFields.includes(field)) {
        return { entityFields: state.entityFields.filter((f) => f !== field) };
      } else {
        return { entityFields: [...state.entityFields, field] };
      }
    });
  },

  setSaveMapper: (saveMapper) => set({ saveMapper }),
  setTimeStart: (timeStart) => set({ timeStart }),
  setTimeEnd: (timeEnd) => set({ timeEnd }),

  // Results
  setResult: (fileId, result) => {
    set((state) => ({
      results: { ...state.results, [fileId]: result },
    }));
  },

  setIngesting: (isIngesting) => set({ isIngesting }),
  setIngestError: (ingestError) => set({ ingestError }),
  setCurrentIngestIndex: (currentIngestIndex) => set({ currentIngestIndex }),

  // Navigation
  nextStep: () => {
    const { step } = get();
    const currentIndex = STEP_ORDER.indexOf(step);
    if (currentIndex < STEP_ORDER.length - 1) {
      set({ step: STEP_ORDER[currentIndex + 1] });
    }
  },

  prevStep: () => {
    const { step } = get();
    const currentIndex = STEP_ORDER.indexOf(step);
    if (currentIndex > 0) {
      set({ step: STEP_ORDER[currentIndex - 1] });
    }
  },

  goToStep: (step) => set({ step }),

  reset: () => set(initialState),

  // Computed
  canProceed: () => {
    const { step, files, fieldMappings } = get();

    switch (step) {
      case "files": {
        // Need at least one file with source and query name
        const validFiles = files.filter(
          (f) => f.file && f.source.trim() && f.queryName.trim()
        );
        return validFiles.length > 0;
      }
      case "schema": {
        // All files must have previews
        const filesWithPreviews = files.filter((f) => f.previewData !== null);
        return filesWithPreviews.length === files.length && files.length > 0;
      }
      case "mapping": {
        // Must have event_ts and event_type mapped
        const hasTimestamp = Object.values(fieldMappings).includes("event_ts");
        const hasEventType = Object.values(fieldMappings).includes("event_type");
        return hasTimestamp && hasEventType;
      }
      case "entities":
        return true; // Entity selection is optional
      case "confirm":
        return true;
      case "ingesting":
        return false; // Can't proceed while ingesting
      case "complete":
        return false; // End state
      default:
        return false;
    }
  },

  getMappingsArray: () => {
    const { fieldMappings } = get();
    return Object.entries(fieldMappings).map(([source_field, unified_field]) => ({
      source_field,
      unified_field,
    }));
  },

  getFilesWithPreviews: () => {
    const { files } = get();
    return files.filter((f) => f.previewData !== null);
  },

  getTotalRows: () => {
    const { files } = get();
    return files.reduce((sum, f) => sum + (f.previewData?.total_rows || 0), 0);
  },

  getTotalIngested: () => {
    const { results } = get();
    return Object.values(results).reduce((sum, r) => sum + r.events_ingested, 0);
  },

  getTotalSkipped: () => {
    const { results } = get();
    return Object.values(results).reduce((sum, r) => sum + r.events_skipped, 0);
  },
}));
