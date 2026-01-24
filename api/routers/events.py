"""Event-related API endpoints."""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

import sys
from pathlib import Path

# Add app directory to path to import services
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from services.db import list_cases, query_df, time_bounds
from services.filters import build_filters

from api.schemas.events import Event, EventsResponse

router = APIRouter(prefix="/cases/{case_id}/events", tags=["events"])


@router.get("", response_model=EventsResponse)
def get_events(
    case_id: str,
    start_dt: Optional[datetime] = None,
    end_dt: Optional[datetime] = None,
    sources: List[str] = Query(default=[]),
    event_types: List[str] = Query(default=[]),
    hosts: List[str] = Query(default=[]),
    users: List[str] = Query(default=[]),
    ips: List[str] = Query(default=[]),
    processes: List[str] = Query(default=[]),
    hashes: List[str] = Query(default=[]),
    severity: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort_by: str = Query(default="event_ts", enum=["event_ts", "-event_ts"]),
):
    """
    Get events for a case with multi-entity filter support.

    Supports filtering by multiple hosts, users, IPs, etc. with AND logic.
    """
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    # Get time bounds if not specified
    min_ts, max_ts = time_bounds(case_id)
    if not min_ts:
        return EventsResponse(events=[], total=0, page=page, page_size=page_size, total_pages=0)

    if not start_dt:
        start_dt = min_ts
    if not end_dt:
        end_dt = max_ts

    # Make timezone-aware if needed
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    # Build filters
    where_clause, params = build_filters(
        case_id,
        start_dt,
        end_dt,
        sources,
        event_types,
        hosts,
        users,
        ips,
        processes,
        hashes,
    )

    # Add severity filter if specified
    if severity:
        where_clause += " AND e.severity = ?"
        params.append(severity)

    # Get total count
    count_result = query_df(
        case_id,
        f"SELECT COUNT(*) as cnt FROM events e WHERE {where_clause}",
        tuple(params),
    )
    total = int(count_result.iloc[0]["cnt"]) if not count_result.empty else 0
    total_pages = max(1, (total + page_size - 1) // page_size)

    # Build sort clause
    sort_clause = "e.event_ts ASC" if sort_by == "event_ts" else "e.event_ts DESC"

    # Query events with pagination
    offset = (page - 1) * page_size
    events_df = query_df(
        case_id,
        f"""
        SELECT
          e.event_pk, e.event_ts, e.source_system, e.event_type, e.host, e.user,
          e.src_ip, e.dest_ip, e.src_port, e.dest_port,
          e.process_name, e.process_cmdline, e.process_id, e.parent_pid,
          e.parent_process_name, e.parent_process_cmdline,
          e.file_path, e.file_hash,
          e.registry_hive, e.registry_key, e.registry_value_name,
          e.registry_value_type, e.registry_value_data,
          e.url, e.dns_query,
          e.tactic, e.technique, e.outcome, e.severity, e.message,
          e.source_event_id, e.raw_ref, e.raw_json, e.run_id
        FROM events e
        WHERE {where_clause}
        ORDER BY {sort_clause}
        LIMIT ? OFFSET ?
        """,
        tuple(params + [page_size, offset]),
    )

    events = []
    for _, row in events_df.iterrows():
        event_dict = row.to_dict()
        # Handle raw_json (might be string)
        if isinstance(event_dict.get("raw_json"), str):
            import json
            try:
                event_dict["raw_json"] = json.loads(event_dict["raw_json"])
            except (json.JSONDecodeError, TypeError):
                event_dict["raw_json"] = None
        events.append(Event(**event_dict))

    return EventsResponse(
        events=events,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{event_pk}", response_model=Event)
def get_event(case_id: str, event_pk: int):
    """Get a single event by primary key."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    event_df = query_df(
        case_id,
        """
        SELECT *
        FROM events
        WHERE case_id = ? AND event_pk = ?
        """,
        (case_id, event_pk),
    )

    if event_df.empty:
        raise HTTPException(status_code=404, detail=f"Event {event_pk} not found")

    event_dict = event_df.iloc[0].to_dict()
    if isinstance(event_dict.get("raw_json"), str):
        import json
        try:
            event_dict["raw_json"] = json.loads(event_dict["raw_json"])
        except (json.JSONDecodeError, TypeError):
            event_dict["raw_json"] = None

    return Event(**event_dict)
