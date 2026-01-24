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
