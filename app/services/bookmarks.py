from __future__ import annotations

import sqlite3
from typing import Set

from services.db import db_path, now_utc_iso, query_df, table_exists


def toggle_bookmark(case_id: str, event_pk: int, label: str = "") -> bool:
    """Toggle bookmark for an event. Returns True if bookmarked, False if removed."""
    with sqlite3.connect(db_path(case_id)) as conn:
        existing = conn.execute(
            "SELECT bookmark_id FROM bookmarked_events WHERE case_id = ? AND event_pk = ?",
            (case_id, event_pk),
        ).fetchone()
        if existing:
            conn.execute(
                "DELETE FROM bookmarked_events WHERE case_id = ? AND event_pk = ?",
                (case_id, event_pk),
            )
            return False
        conn.execute(
            """
            INSERT INTO bookmarked_events(case_id, event_pk, label, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, event_pk, label, now_utc_iso()),
        )
        return True


def get_bookmarked_pks(case_id: str) -> Set[int]:
    """Get set of bookmarked event PKs for a case."""
    if not table_exists(case_id, "bookmarked_events"):
        return set()
    df = query_df(case_id, "SELECT event_pk FROM bookmarked_events WHERE case_id = ?", (case_id,))
    return set(df["event_pk"].tolist()) if not df.empty else set()
