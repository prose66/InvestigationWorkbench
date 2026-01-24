"""Timeline marker API endpoints."""
import sqlite3
from typing import List

from fastapi import APIRouter, HTTPException

import sys
from pathlib import Path

# Add app directory to path to import services
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from services.db import list_cases, db_path, table_exists, now_utc_iso, query_df
from services.markers import get_timeline_markers, add_timeline_marker, delete_timeline_marker

from api.schemas.markers import Marker, MarkerCreate

router = APIRouter(prefix="/cases/{case_id}/markers", tags=["markers"])


@router.get("", response_model=List[Marker])
def get_markers(case_id: str):
    """Get all timeline markers for a case."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    markers_df = get_timeline_markers(case_id)
    if markers_df.empty:
        return []

    return [
        Marker(
            marker_id=row["marker_id"],
            marker_ts=row["marker_ts"],
            label=row["label"],
            description=row.get("description"),
            color=row.get("color", "#ff6b6b"),
        )
        for _, row in markers_df.iterrows()
    ]


@router.post("", response_model=Marker)
def create_marker(case_id: str, marker: MarkerCreate):
    """Create a new timeline marker."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    try:
        add_timeline_marker(
            case_id,
            marker.marker_ts,
            marker.label,
            marker.description or "",
            marker.color,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get the created marker
    markers_df = get_timeline_markers(case_id)
    if markers_df.empty:
        raise HTTPException(status_code=500, detail="Failed to create marker")

    # Return the most recent marker (should be the one we just created)
    row = markers_df.iloc[-1]
    return Marker(
        marker_id=int(row["marker_id"]),
        marker_ts=row["marker_ts"],
        label=row["label"],
        description=row.get("description"),
        color=row.get("color", "#ff6b6b"),
    )


@router.delete("/{marker_id}")
def remove_marker(case_id: str, marker_id: int):
    """Delete a timeline marker."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    if not table_exists(case_id, "timeline_markers"):
        raise HTTPException(status_code=404, detail="Marker not found")

    # Check marker exists
    markers_df = get_timeline_markers(case_id)
    if markers_df.empty or marker_id not in markers_df["marker_id"].values:
        raise HTTPException(status_code=404, detail="Marker not found")

    delete_timeline_marker(case_id, marker_id)
    return {"message": "Marker deleted"}
