"""Bookmark-related API endpoints."""
import sqlite3
from typing import List

from fastapi import APIRouter, HTTPException

import sys
from pathlib import Path

# Add app directory to path to import services
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from services.db import list_cases, db_path, query_df, table_exists, now_utc_iso

from api.schemas.bookmarks import Bookmark, BookmarkCreate, BookmarkUpdate

router = APIRouter(prefix="/cases/{case_id}/bookmarks", tags=["bookmarks"])


@router.get("", response_model=List[Bookmark])
def get_bookmarks(case_id: str):
    """Get all bookmarks for a case."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    if not table_exists(case_id, "bookmarked_events"):
        return []

    bookmarks_df = query_df(
        case_id,
        """
        SELECT b.bookmark_id, b.event_pk, b.label, b.notes, b.created_at,
               e.event_ts, e.source_system, e.event_type, e.host, e.user, e.message
        FROM bookmarked_events b
        JOIN events e ON b.event_pk = e.event_pk
        WHERE b.case_id = ?
        ORDER BY e.event_ts DESC
        """,
        (case_id,),
    )

    return [
        Bookmark(
            bookmark_id=row["bookmark_id"],
            event_pk=row["event_pk"],
            label=row["label"],
            notes=row["notes"],
            created_at=row["created_at"],
            event_ts=row["event_ts"],
            source_system=row["source_system"],
            event_type=row["event_type"],
            host=row["host"],
            user=row["user"],
            message=row["message"],
        )
        for _, row in bookmarks_df.iterrows()
    ]


@router.post("", response_model=Bookmark)
def create_bookmark(case_id: str, bookmark: BookmarkCreate):
    """Create a new bookmark."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    # Verify event exists
    event_df = query_df(
        case_id,
        "SELECT event_pk FROM events WHERE case_id = ? AND event_pk = ?",
        (case_id, bookmark.event_pk),
    )
    if event_df.empty:
        raise HTTPException(status_code=404, detail=f"Event {bookmark.event_pk} not found")

    # Check if already bookmarked
    if table_exists(case_id, "bookmarked_events"):
        existing = query_df(
            case_id,
            "SELECT bookmark_id FROM bookmarked_events WHERE case_id = ? AND event_pk = ?",
            (case_id, bookmark.event_pk),
        )
        if not existing.empty:
            raise HTTPException(status_code=400, detail="Event already bookmarked")

    # Create bookmark
    created_at = now_utc_iso()
    with sqlite3.connect(db_path(case_id)) as conn:
        cursor = conn.execute(
            """
            INSERT INTO bookmarked_events(case_id, event_pk, label, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (case_id, bookmark.event_pk, bookmark.label, bookmark.notes, created_at),
        )
        bookmark_id = cursor.lastrowid

    # Return full bookmark with event details
    bookmarks_df = query_df(
        case_id,
        """
        SELECT b.bookmark_id, b.event_pk, b.label, b.notes, b.created_at,
               e.event_ts, e.source_system, e.event_type, e.host, e.user, e.message
        FROM bookmarked_events b
        JOIN events e ON b.event_pk = e.event_pk
        WHERE b.bookmark_id = ?
        """,
        (bookmark_id,),
    )
    row = bookmarks_df.iloc[0]

    return Bookmark(
        bookmark_id=row["bookmark_id"],
        event_pk=row["event_pk"],
        label=row["label"],
        notes=row["notes"],
        created_at=row["created_at"],
        event_ts=row["event_ts"],
        source_system=row["source_system"],
        event_type=row["event_type"],
        host=row["host"],
        user=row["user"],
        message=row["message"],
    )


@router.put("/{bookmark_id}", response_model=Bookmark)
def update_bookmark(case_id: str, bookmark_id: int, update: BookmarkUpdate):
    """Update a bookmark's label and notes."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    if not table_exists(case_id, "bookmarked_events"):
        raise HTTPException(status_code=404, detail="Bookmark not found")

    # Check bookmark exists
    existing = query_df(
        case_id,
        "SELECT bookmark_id FROM bookmarked_events WHERE case_id = ? AND bookmark_id = ?",
        (case_id, bookmark_id),
    )
    if existing.empty:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    # Update
    with sqlite3.connect(db_path(case_id)) as conn:
        conn.execute(
            "UPDATE bookmarked_events SET label = ?, notes = ? WHERE bookmark_id = ?",
            (update.label, update.notes, bookmark_id),
        )

    # Return updated bookmark
    bookmarks_df = query_df(
        case_id,
        """
        SELECT b.bookmark_id, b.event_pk, b.label, b.notes, b.created_at,
               e.event_ts, e.source_system, e.event_type, e.host, e.user, e.message
        FROM bookmarked_events b
        JOIN events e ON b.event_pk = e.event_pk
        WHERE b.bookmark_id = ?
        """,
        (bookmark_id,),
    )
    row = bookmarks_df.iloc[0]

    return Bookmark(
        bookmark_id=row["bookmark_id"],
        event_pk=row["event_pk"],
        label=row["label"],
        notes=row["notes"],
        created_at=row["created_at"],
        event_ts=row["event_ts"],
        source_system=row["source_system"],
        event_type=row["event_type"],
        host=row["host"],
        user=row["user"],
        message=row["message"],
    )


@router.delete("/{bookmark_id}")
def delete_bookmark(case_id: str, bookmark_id: int):
    """Delete a bookmark."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    if not table_exists(case_id, "bookmarked_events"):
        raise HTTPException(status_code=404, detail="Bookmark not found")

    # Check bookmark exists
    existing = query_df(
        case_id,
        "SELECT bookmark_id FROM bookmarked_events WHERE case_id = ? AND bookmark_id = ?",
        (case_id, bookmark_id),
    )
    if existing.empty:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    with sqlite3.connect(db_path(case_id)) as conn:
        conn.execute(
            "DELETE FROM bookmarked_events WHERE case_id = ? AND bookmark_id = ?",
            (case_id, bookmark_id),
        )

    return {"message": "Bookmark deleted"}
