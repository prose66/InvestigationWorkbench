"""Search API endpoints."""
from typing import List

from fastapi import APIRouter, HTTPException, Query

import sys
from pathlib import Path

# Add app directory to path to import services
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from services.db import list_cases
from services.search import search_events, count_search_results

from api.schemas.events import Event

router = APIRouter(prefix="/cases/{case_id}/search", tags=["search"])


class SearchResponse:
    """Response for search results."""

    def __init__(self, events: List[Event], total: int, query: str):
        self.events = events
        self.total = total
        self.query = query


@router.get("")
def search(
    case_id: str,
    q: str = Query(..., min_length=1, description="Search keyword"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Search events by keyword across multiple fields."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    results_df = search_events(case_id, q, limit=limit)
    total = count_search_results(case_id, q)

    events = []
    for _, row in results_df.iterrows():
        events.append(
            Event(
                event_pk=row["event_pk"],
                event_ts=row["event_ts"],
                source_system=row["source_system"],
                event_type=row["event_type"],
                host=row.get("host"),
                user=row.get("user"),
                src_ip=row.get("src_ip"),
                dest_ip=row.get("dest_ip"),
                process_name=row.get("process_name"),
                outcome=row.get("outcome"),
                severity=row.get("severity"),
                message=row.get("message"),
            )
        )

    return {
        "events": events,
        "total": total,
        "query": q,
        "returned": len(events),
    }
