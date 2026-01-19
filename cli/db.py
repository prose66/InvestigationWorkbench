from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path, schema_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        schema_sql = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
