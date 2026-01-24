"""Event-related Pydantic models."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Event(BaseModel):
    """A normalized security event."""

    event_pk: int
    event_ts: str
    source_system: str
    event_type: str
    host: Optional[str] = None
    user: Optional[str] = None
    src_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    src_port: Optional[int] = None
    dest_port: Optional[int] = None
    process_name: Optional[str] = None
    process_cmdline: Optional[str] = None
    process_id: Optional[int] = None
    parent_pid: Optional[int] = None
    parent_process_name: Optional[str] = None
    parent_process_cmdline: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    registry_hive: Optional[str] = None
    registry_key: Optional[str] = None
    registry_value_name: Optional[str] = None
    registry_value_type: Optional[str] = None
    registry_value_data: Optional[str] = None
    url: Optional[str] = None
    dns_query: Optional[str] = None
    tactic: Optional[str] = None
    technique: Optional[str] = None
    outcome: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    source_event_id: Optional[str] = None
    raw_ref: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None
    run_id: Optional[str] = None
    score: Optional[float] = None

    class Config:
        from_attributes = True


class EventFilter(BaseModel):
    """Filters for querying events."""

    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    sources: List[str] = Field(default_factory=list)
    event_types: List[str] = Field(default_factory=list)
    hosts: List[str] = Field(default_factory=list)
    users: List[str] = Field(default_factory=list)
    ips: List[str] = Field(default_factory=list)
    processes: List[str] = Field(default_factory=list)
    hashes: List[str] = Field(default_factory=list)
    severity: Optional[str] = None
    keyword: Optional[str] = None


class EventsResponse(BaseModel):
    """Paginated response for events."""

    events: List[Event]
    total: int
    page: int
    page_size: int
    total_pages: int
