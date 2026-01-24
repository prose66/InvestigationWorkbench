"""Case-related Pydantic models."""
from typing import List, Optional

from pydantic import BaseModel


class Case(BaseModel):
    """A case identifier."""

    case_id: str


class CaseSummary(BaseModel):
    """Summary statistics for a case."""

    case_id: str
    total_events: int
    total_runs: int
    total_sources: int
    total_hosts: int
    min_ts: Optional[str] = None
    max_ts: Optional[str] = None
    source_systems: List[str] = []
    event_types: List[str] = []


class QueryRun(BaseModel):
    """A query run that ingested events."""

    run_id: str
    source_system: str
    query_name: str
    executed_at: str
    time_start: str
    time_end: str
    row_count: int
