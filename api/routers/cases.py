"""Case-related API endpoints."""
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.services.db import list_cases, query_one, query_df, time_bounds, distinct_values, delete_case
from api.schemas.cases import Case, CaseSummary, QueryRun
from cli.commands import init_case


class CreateCaseRequest(BaseModel):
    case_id: str
    title: Optional[str] = None

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=List[Case])
def get_cases():
    """List all available cases."""
    case_ids = list_cases()
    return [Case(case_id=cid) for cid in case_ids]


@router.post("", response_model=Case, status_code=201)
def create_case(request: CreateCaseRequest):
    """Create a new case."""
    case_id = request.case_id.strip()

    # Validate case_id format (alphanumeric, hyphens, underscores)
    if not re.match(r"^[a-zA-Z0-9_-]+$", case_id):
        raise HTTPException(
            status_code=400,
            detail="Case ID must contain only alphanumeric characters, hyphens, and underscores"
        )

    if len(case_id) < 1 or len(case_id) > 64:
        raise HTTPException(
            status_code=400,
            detail="Case ID must be between 1 and 64 characters"
        )

    # Check if case already exists
    if case_id in list_cases():
        raise HTTPException(status_code=409, detail=f"Case '{case_id}' already exists")

    # Create the case using CLI command
    init_case(case_id, request.title)

    return Case(case_id=case_id)


@router.delete("/{case_id}", status_code=204)
def remove_case(case_id: str):
    """Delete a case and all its data."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    if not delete_case(case_id):
        raise HTTPException(status_code=500, detail="Failed to delete case")

    return None


@router.get("/{case_id}/summary", response_model=CaseSummary)
def get_case_summary(case_id: str):
    """Get summary statistics for a case."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    summary = query_one(
        case_id,
        """
        SELECT COUNT(*) AS total_events,
               COUNT(DISTINCT run_id) AS total_runs,
               COUNT(DISTINCT source_system) AS total_sources,
               COUNT(DISTINCT host) AS total_hosts
        FROM events
        WHERE case_id = ?
        """,
        (case_id,),
    )

    min_ts, max_ts = time_bounds(case_id)
    source_systems = distinct_values(case_id, "source_system")
    event_types = distinct_values(case_id, "event_type", limit=50)

    return CaseSummary(
        case_id=case_id,
        total_events=summary["total_events"] if summary else 0,
        total_runs=summary["total_runs"] if summary else 0,
        total_sources=summary["total_sources"] if summary else 0,
        total_hosts=summary["total_hosts"] if summary else 0,
        min_ts=min_ts.isoformat() if min_ts else None,
        max_ts=max_ts.isoformat() if max_ts else None,
        source_systems=source_systems,
        event_types=event_types,
    )


@router.get("/{case_id}/runs", response_model=List[QueryRun])
def get_query_runs(case_id: str):
    """Get all query runs for a case."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    runs_df = query_df(
        case_id,
        """
        SELECT run_id, source_system, query_name, executed_at, time_start, time_end, row_count
        FROM query_runs
        WHERE case_id = ?
        ORDER BY executed_at DESC
        """,
        (case_id,),
    )

    return [
        QueryRun(
            run_id=row["run_id"],
            source_system=row["source_system"],
            query_name=row["query_name"],
            executed_at=row["executed_at"],
            time_start=row["time_start"],
            time_end=row["time_end"],
            row_count=row["row_count"],
        )
        for _, row in runs_df.iterrows()
    ]
