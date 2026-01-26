// API Types

export interface Case {
  case_id: string;
}

export interface CaseSummary {
  case_id: string;
  total_events: number;
  total_runs: number;
  total_sources: number;
  total_hosts: number;
  min_ts: string | null;
  max_ts: string | null;
  source_systems: string[];
  event_types: string[];
}

export interface Event {
  event_pk: number;
  event_ts: string;
  source_system: string;
  event_type: string;
  host?: string;
  user?: string;
  src_ip?: string;
  dest_ip?: string;
  src_port?: number;
  dest_port?: number;
  process_name?: string;
  process_cmdline?: string;
  process_id?: number;
  parent_pid?: number;
  parent_process_name?: string;
  parent_process_cmdline?: string;
  file_path?: string;
  file_hash?: string;
  registry_hive?: string;
  registry_key?: string;
  registry_value_name?: string;
  registry_value_type?: string;
  registry_value_data?: string;
  url?: string;
  dns_query?: string;
  tactic?: string;
  technique?: string;
  outcome?: string;
  severity?: string;
  message?: string;
  source_event_id?: string;
  raw_ref?: string;
  raw_json?: Record<string, unknown>;
  run_id?: string;
  score?: number;
}

export interface EventsResponse {
  events: Event[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Entity {
  entity_type: string;
  entity_value: string;
  first_seen?: string;
  last_seen?: string;
  event_count: number;
}

export interface EntitySummary {
  entity_type: string;
  entity_value: string;
  first_seen: string;
  last_seen: string;
  total_events: number;
  source_systems: string[];
  event_types: string[];
}

export interface RelatedEntity {
  entity_type: string;
  entity_value: string;
  count: number;
  first_seen: string;
  last_seen: string;
}

export interface EntityRelationships {
  entity_type: string;
  entity_value: string;
  related_hosts: RelatedEntity[];
  related_users: RelatedEntity[];
  related_ips: RelatedEntity[];
  related_processes: RelatedEntity[];
  related_hashes: RelatedEntity[];
}

export interface Bookmark {
  bookmark_id: number;
  event_pk: number;
  label?: string;
  notes?: string;
  created_at: string;
  event_ts?: string;
  source_system?: string;
  event_type?: string;
  host?: string;
  user?: string;
  message?: string;
}

export interface Marker {
  marker_id: number;
  marker_ts: string;
  label: string;
  description?: string;
  color: string;
}

export interface GraphNode {
  id: string;
  label: string;
  entity_type: string;
  event_count: number;
  first_seen: string;
  last_seen: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  edge_type: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CoverageGap {
  start: string;
  end: string;
  duration_hours: number;
  expected_events: number;
  severity: string;
  affected_sources: string[];
}

export interface SourceCoverage {
  source_system: string;
  first_event: string;
  last_event: string;
  event_count: number;
  active_hours: number;
  coverage_pct: number;
}

export interface SearchResponse {
  events: Event[];
  total: number;
  query: string;
  returned: number;
}

// Pivot entity for multi-filter support
export interface PivotEntity {
  type: string;
  column: string;
  value: string;
}

// Entity types
export const ENTITY_TYPES = ["host", "user", "ip", "hash", "process"] as const;
export type EntityType = (typeof ENTITY_TYPES)[number];

// Ingest types
export interface FieldMapping {
  source_field: string;
  unified_field: string | null; // null = ignore
  transform?: { format?: string; type?: string };
}

export interface PreviewResponse {
  source_fields: string[];
  preview_rows: Record<string, unknown>[];
  total_rows: number;
  suggested_mappings: Record<string, string>;
  file_format: "ndjson" | "csv";
  mapper_type: string;
}

export interface IngestRequest {
  source: string;
  query_name: string;
  content: string; // Base64 encoded
  filename: string;
  field_mappings: FieldMapping[];
  entity_fields: string[];
  save_mapper: boolean;
  time_start?: string;
  time_end?: string;
}

export interface IngestResponse {
  run_id: string;
  events_ingested: number;
  events_skipped: number;
  errors: Array<{ line?: number; error: string; sample?: Record<string, unknown> }>;
  suggestions: string[];
  mapper_saved: boolean;
}

export interface MapperInfo {
  name: string;
  type: "yaml_case" | "yaml_builtin" | "builtin";
  description?: string;
  source: string;
  field_count: number;
}

export interface UnifiedField {
  name: string;
  required: boolean;
}

// Batch ingest types
export interface FileEntry {
  id: string;
  file: File;
  source: string;
  queryName: string;
  previewData: PreviewResponse | null;
  isLoading: boolean;
  error: string | null;
}

export interface BatchPreviewRequest {
  files: Array<{
    source: string;
    content: string;
    filename: string;
  }>;
}

export interface BatchPreviewResponse {
  file_previews: PreviewResponse[];
  merged_fields: string[];
  field_sources: Record<string, number[]>; // field → file indices
  suggested_mappings: Record<string, string>;
}

export interface BatchIngestRequest {
  files: Array<{
    source: string;
    query_name: string;
    content: string;
    filename: string;
  }>;
  field_mappings: FieldMapping[];
  entity_fields: string[];
  save_mapper: boolean;
  time_start?: string;
  time_end?: string;
}

export interface BatchIngestResponse {
  results: IngestResponse[];
  total_ingested: number;
  total_skipped: number;
}
