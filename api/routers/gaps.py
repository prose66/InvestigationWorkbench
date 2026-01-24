"""Coverage gap API endpoints."""
from typing import List

from fastapi import APIRouter, HTTPException, Query

import sys
from pathlib import Path

# Add app directory to path to import services
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from services.db import list_cases
from services.gaps import detect_timeline_gaps, get_source_coverage

from api.schemas.gaps import CoverageGap, SourceCoverage

router = APIRouter(prefix="/cases/{case_id}", tags=["coverage"])


@router.get("/gaps", response_model=List[CoverageGap])
def get_gaps(
    case_id: str,
    bucket_minutes: int = Query(default=60, ge=15, le=1440),
    min_gap_buckets: int = Query(default=2, ge=1),
    source: str = Query(default=None),
):
    """Detect gaps in event coverage."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    _, gaps = detect_timeline_gaps(
        case_id,
        bucket_minutes=bucket_minutes,
        min_gap_buckets=min_gap_buckets,
        source_filter=source,
    )

    return [
        CoverageGap(
            start=g.start.isoformat(),
            end=g.end.isoformat(),
            duration_hours=g.duration.total_seconds() / 3600,
            expected_events=g.expected_events,
            severity=g.severity,
            affected_sources=g.affected_sources,
        )
        for g in gaps
    ]


@router.get("/coverage", response_model=List[SourceCoverage])
def get_coverage(case_id: str):
    """Get coverage statistics for each source system."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    coverage_df = get_source_coverage(case_id)

    if coverage_df.empty:
        return []

    return [
        SourceCoverage(
            source_system=row["source_system"],
            first_event=row["first_event"],
            last_event=row["last_event"],
            event_count=int(row["event_count"]),
            active_hours=int(row["active_hours"]),
            coverage_pct=float(row["coverage_pct"]),
        )
        for _, row in coverage_df.iterrows()
    ]
