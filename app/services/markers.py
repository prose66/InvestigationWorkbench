from __future__ import annotations

import sqlite3
import pandas as pd

from services.db import db_path, now_utc_iso, query_df, table_exists


def add_timeline_marker(case_id: str, marker_ts: str, label: str, description: str = "", color: str = "#ff6b6b") -> None:
    with sqlite3.connect(db_path(case_id)) as conn:
        conn.execute(
            """
            INSERT INTO timeline_markers(case_id, marker_ts, label, description, color, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (case_id, marker_ts, label, description, color, now_utc_iso()),
        )


def get_timeline_markers(case_id: str) -> pd.DataFrame:
    if not table_exists(case_id, "timeline_markers"):
        return pd.DataFrame()
    return query_df(
        case_id,
        "SELECT marker_id, marker_ts, label, description, color FROM timeline_markers WHERE case_id = ?",
        (case_id,),
    )


def delete_timeline_marker(case_id: str, marker_id: int) -> None:
    with sqlite3.connect(db_path(case_id)) as conn:
        conn.execute("DELETE FROM timeline_markers WHERE case_id = ? AND marker_id = ?", (case_id, marker_id))
