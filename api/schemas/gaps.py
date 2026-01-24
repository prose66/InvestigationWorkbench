"""Coverage gap Pydantic models."""
from typing import List, Optional

from pydantic import BaseModel


class CoverageGap(BaseModel):
    """A gap in event coverage."""

    start: str
    end: str
    duration_hours: float
    expected_events: int
    severity: str
    affected_sources: List[str]


class SourceCoverage(BaseModel):
    """Coverage statistics for a source system."""

    source_system: str
    first_event: str
    last_event: str
    event_count: int
    active_hours: int
    coverage_pct: float
