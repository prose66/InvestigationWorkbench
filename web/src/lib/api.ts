// API Client for Investigation Workbench

import type {
  Case,
  CaseSummary,
  Event,
  EventsResponse,
  Entity,
  EntitySummary,
  EntityRelationships,
  Bookmark,
  Marker,
  GraphResponse,
  CoverageGap,
  SourceCoverage,
  SearchResponse,
  EntityType,
  PreviewResponse,
  IngestRequest,
  IngestResponse,
  MapperInfo,
  UnifiedField,
  BatchPreviewRequest,
  BatchPreviewResponse,
  BatchIngestRequest,
  BatchIngestResponse,
} from "./types";

const API_BASE = "/api";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Cases
export async function getCases(): Promise<Case[]> {
  return fetchJSON(`${API_BASE}/cases`);
}

export async function getCaseSummary(caseId: string): Promise<CaseSummary> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/summary`);
}

// Events
export interface EventFilterParams {
  start_dt?: string;
  end_dt?: string;
  sources?: string[];
  event_types?: string[];
  hosts?: string[];
  users?: string[];
  ips?: string[];
  processes?: string[];
  hashes?: string[];
  severity?: string;
  page?: number;
  page_size?: number;
  sort_by?: "event_ts" | "-event_ts";
}

export async function getEvents(
  caseId: string,
  filters: EventFilterParams = {}
): Promise<EventsResponse> {
  const params = new URLSearchParams();

  if (filters.start_dt) params.append("start_dt", filters.start_dt);
  if (filters.end_dt) params.append("end_dt", filters.end_dt);
  if (filters.severity) params.append("severity", filters.severity);
  if (filters.page) params.append("page", filters.page.toString());
  if (filters.page_size) params.append("page_size", filters.page_size.toString());
  if (filters.sort_by) params.append("sort_by", filters.sort_by);

  // Multi-value filters
  filters.sources?.forEach((s) => params.append("sources", s));
  filters.event_types?.forEach((t) => params.append("event_types", t));
  filters.hosts?.forEach((h) => params.append("hosts", h));
  filters.users?.forEach((u) => params.append("users", u));
  filters.ips?.forEach((i) => params.append("ips", i));
  filters.processes?.forEach((p) => params.append("processes", p));
  filters.hashes?.forEach((h) => params.append("hashes", h));

  const queryString = params.toString();
  return fetchJSON(`${API_BASE}/cases/${caseId}/events${queryString ? `?${queryString}` : ""}`);
}

export async function getEvent(caseId: string, eventPk: number): Promise<Event> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/events/${eventPk}`);
}

// Entities
export async function getEntities(
  caseId: string,
  entityType: EntityType,
  limit = 100
): Promise<Entity[]> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/entities?entity_type=${entityType}&limit=${limit}`);
}

export async function getEntitySummary(
  caseId: string,
  entityType: string,
  entityValue: string
): Promise<EntitySummary> {
  return fetchJSON(
    `${API_BASE}/cases/${caseId}/entity/${entityType}/${encodeURIComponent(entityValue)}`
  );
}

export async function getEntityRelationships(
  caseId: string,
  entityType: string,
  entityValue: string,
  limit = 15
): Promise<EntityRelationships> {
  return fetchJSON(
    `${API_BASE}/cases/${caseId}/entity/${entityType}/${encodeURIComponent(entityValue)}/related?limit=${limit}`
  );
}

// Bookmarks
export async function getBookmarks(caseId: string): Promise<Bookmark[]> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/bookmarks`);
}

export async function createBookmark(
  caseId: string,
  eventPk: number,
  label?: string,
  notes?: string
): Promise<Bookmark> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/bookmarks`, {
    method: "POST",
    body: JSON.stringify({ event_pk: eventPk, label, notes }),
  });
}

export async function updateBookmark(
  caseId: string,
  bookmarkId: number,
  label?: string,
  notes?: string
): Promise<Bookmark> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/bookmarks/${bookmarkId}`, {
    method: "PUT",
    body: JSON.stringify({ label, notes }),
  });
}

export async function deleteBookmark(caseId: string, bookmarkId: number): Promise<void> {
  await fetchJSON(`${API_BASE}/cases/${caseId}/bookmarks/${bookmarkId}`, {
    method: "DELETE",
  });
}

// Markers
export async function getMarkers(caseId: string): Promise<Marker[]> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/markers`);
}

export async function createMarker(
  caseId: string,
  markerTs: string,
  label: string,
  description?: string,
  color?: string
): Promise<Marker> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/markers`, {
    method: "POST",
    body: JSON.stringify({
      marker_ts: markerTs,
      label,
      description,
      color: color || "#ff6b6b",
    }),
  });
}

export async function deleteMarker(caseId: string, markerId: number): Promise<void> {
  await fetchJSON(`${API_BASE}/cases/${caseId}/markers/${markerId}`, {
    method: "DELETE",
  });
}

// Search
export async function searchEvents(
  caseId: string,
  query: string,
  limit = 100
): Promise<SearchResponse> {
  return fetchJSON(
    `${API_BASE}/cases/${caseId}/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
}

// Graph
export async function getEntityGraph(
  caseId: string,
  entityType: string,
  entityValue: string,
  maxNodes = 50,
  minEdgeWeight = 1
): Promise<GraphResponse> {
  return fetchJSON(
    `${API_BASE}/cases/${caseId}/graph?entity_type=${entityType}&entity_value=${encodeURIComponent(entityValue)}&max_nodes=${maxNodes}&min_edge_weight=${minEdgeWeight}`
  );
}

// Coverage
export async function getCoverageGaps(
  caseId: string,
  bucketMinutes = 60,
  minGapBuckets = 2,
  source?: string
): Promise<CoverageGap[]> {
  const params = new URLSearchParams({
    bucket_minutes: bucketMinutes.toString(),
    min_gap_buckets: minGapBuckets.toString(),
  });
  if (source) params.append("source", source);

  return fetchJSON(`${API_BASE}/cases/${caseId}/gaps?${params}`);
}

export async function getSourceCoverage(caseId: string): Promise<SourceCoverage[]> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/coverage`);
}

// Ingest
export async function uploadPreview(
  caseId: string,
  source: string,
  content: string,
  filename: string
): Promise<PreviewResponse> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/ingest/preview`, {
    method: "POST",
    body: JSON.stringify({ source, content, filename }),
  });
}

export async function commitIngest(
  caseId: string,
  request: IngestRequest
): Promise<IngestResponse> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/ingest/commit`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getMappers(caseId: string): Promise<MapperInfo[]> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/ingest/mappers`);
}

export async function getUnifiedFields(): Promise<{ fields: UnifiedField[] }> {
  // Use a dummy case_id since unified fields are global
  return fetchJSON(`${API_BASE}/cases/_/ingest/unified-fields`);
}

// Batch Ingest
export async function batchPreview(
  caseId: string,
  files: BatchPreviewRequest["files"]
): Promise<BatchPreviewResponse> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/ingest/preview-batch`, {
    method: "POST",
    body: JSON.stringify({ files }),
  });
}

export async function batchCommit(
  caseId: string,
  request: BatchIngestRequest
): Promise<BatchIngestResponse> {
  return fetchJSON(`${API_BASE}/cases/${caseId}/ingest/commit-batch`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}
