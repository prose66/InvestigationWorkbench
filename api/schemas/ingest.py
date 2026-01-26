"""Ingest-related Pydantic models."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FieldMapping(BaseModel):
    """A single field mapping from source to unified schema."""
    source_field: str
    unified_field: Optional[str] = None  # None = ignore this field
    transform: Optional[Dict[str, str]] = None  # {format, type}


class PreviewRequest(BaseModel):
    """Request to preview file ingestion."""
    source: str = Field(..., description="Source system name (e.g., 'splunk', 'firewall')")
    content: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Original filename for format detection")


class PreviewResponse(BaseModel):
    """Response with preview data and suggested mappings."""
    source_fields: List[str]
    preview_rows: List[Dict[str, Any]]  # First 50 rows
    total_rows: int
    suggested_mappings: Dict[str, str]  # source_field -> unified_field
    file_format: str  # "ndjson" | "csv"
    mapper_type: str  # "yaml_case", "yaml_builtin", "builtin", "generic"


class IngestRequest(BaseModel):
    """Request to commit an ingestion."""
    source: str = Field(..., description="Source system name")
    query_name: str = Field(..., description="Human-readable name for this query/export")
    content: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Original filename")
    field_mappings: List[FieldMapping] = Field(default_factory=list)
    entity_fields: List[str] = Field(default_factory=list, description="Fields to extract as entities")
    save_mapper: bool = Field(default=False, description="Save as YAML mapper for reuse")
    time_start: Optional[str] = Field(None, description="Query time range start (ISO8601)")
    time_end: Optional[str] = Field(None, description="Query time range end (ISO8601)")


class IngestResponse(BaseModel):
    """Response after ingestion completes."""
    run_id: str
    events_ingested: int
    events_skipped: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    mapper_saved: bool = False


class MapperInfo(BaseModel):
    """Information about an available mapper."""
    name: str
    type: str  # "yaml_case", "yaml_builtin", "builtin"
    description: Optional[str] = None
    source: str  # Source system this mapper handles
    field_count: int  # Number of fields mapped


# Batch ingest models
class FilePreview(BaseModel):
    """Single file info for batch preview."""
    source: str
    content: str  # Base64 encoded
    filename: str


class BatchPreviewRequest(BaseModel):
    """Request to preview multiple files."""
    files: List[FilePreview]


class BatchPreviewResponse(BaseModel):
    """Response with merged schema from all files."""
    file_previews: List[PreviewResponse]
    merged_fields: List[str]  # Union of all fields
    field_sources: Dict[str, List[int]]  # field -> file indices
    suggested_mappings: Dict[str, str]  # Unified suggestions


class FileIngestConfig(BaseModel):
    """Single file config for batch ingest."""
    source: str
    query_name: str
    content: str  # Base64 encoded
    filename: str


class BatchIngestRequest(BaseModel):
    """Request to commit multiple files with shared mappings."""
    files: List[FileIngestConfig]
    field_mappings: List[FieldMapping] = Field(default_factory=list)
    entity_fields: List[str] = Field(default_factory=list)
    save_mapper: bool = Field(default=False)
    time_start: Optional[str] = Field(None)
    time_end: Optional[str] = Field(None)


class BatchIngestResponse(BaseModel):
    """Response after batch ingestion completes."""
    results: List[IngestResponse]
    total_ingested: int
    total_skipped: int
