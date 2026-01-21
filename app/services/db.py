from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT_DIR / "cases"


def list_cases() -> List[str]:
    if not CASES_DIR.exists():
        return []
    case_ids = []
    for path in CASES_DIR.iterdir():
        if path.is_dir() and (path / "case.sqlite").exists():
            case_ids.append(path.name)
    return sorted(case_ids)


def db_path(case_id: str) -> Path:
    return CASES_DIR / case_id / "case.sqlite"


def query_df(case_id: str, sql: str, params: Tuple = ()) -> pd.DataFrame:
    with sqlite3.connect(db_path(case_id)) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def query_one(case_id: str, sql: str, params: Tuple = ()) -> Optional[dict]:
    with sqlite3.connect(db_path(case_id)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def table_exists(case_id: str, table_name: str) -> bool:
    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?"
    row = query_one(case_id, sql, (table_name,))
    return bool(row)


def distinct_values(case_id: str, column: str, limit: int = 200) -> List[str]:
    sql = f"""
        SELECT DISTINCT {column} AS value
        FROM events
        WHERE case_id = ? AND {column} IS NOT NULL AND {column} != ''
        ORDER BY {column}
        LIMIT ?
    """
    df = query_df(case_id, sql, (case_id, limit))
    return df["value"].dropna().tolist()


def time_bounds(case_id: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    row = query_one(
        case_id,
        "SELECT MIN(event_ts) AS min_ts, MAX(event_ts) AS max_ts FROM events WHERE case_id = ?",
        (case_id,),
    )
    if not row or not row["min_ts"]:
        return None, None
    min_ts = datetime.fromisoformat(row["min_ts"].replace("Z", "+00:00"))
    max_ts = datetime.fromisoformat(row["max_ts"].replace("Z", "+00:00"))
    return min_ts, max_ts


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
