from __future__ import annotations

import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Iterable, List, Optional

from cli import ingest as ingest_lib
from cli.db import connect, init_db
from cli.utils import now_utc_iso, normalize_ts, sha256_file

ROOT_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT_DIR / "cases"
SCHEMA_PATH = ROOT_DIR / "cli" / "schema.sql"


def case_paths(case_id: str) -> dict:
    case_dir = CASES_DIR / case_id
    return {
        "case_dir": case_dir,
        "db_path": case_dir / "case.sqlite",
        "raw_base": case_dir / "raw",
        "exports": case_dir / "exports",
        "notes": case_dir / "notes.md",
    }


def init_case(case_id: str, title: Optional[str] = None) -> Path:
    paths = case_paths(case_id)
    for key in ("raw_base", "exports"):
        paths[key].mkdir(parents=True, exist_ok=True)
    if not paths["notes"].exists():
        paths["notes"].write_text(f"# {case_id}\n\n", encoding="utf-8")

    init_db(paths["db_path"], SCHEMA_PATH)
    with connect(paths["db_path"]) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO cases(case_id, title, created_at) VALUES (?, ?, ?)",
            (case_id, title, now_utc_iso()),
        )
    return paths["db_path"]


def add_run(
    case_id: str,
    source: str,
    query_name: str,
    query_text: Optional[str],
    time_start: Optional[str],
    time_end: Optional[str],
    file_path: Path,
    executed_at: Optional[str] = None,
) -> str:
    paths = case_paths(case_id)
    if not paths["db_path"].exists():
        raise FileNotFoundError(f"Case not initialized: {paths['db_path']}")

    run_id = str(uuid.uuid4())
    raw_dir = paths["raw_base"] / source
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest_path = raw_dir / f"{run_id}{file_path.suffix.lower()}"
    shutil.copy2(file_path, dest_path)
    file_hash = sha256_file(dest_path)

    with connect(paths["db_path"]) as conn:
        conn.execute(
            """
            INSERT INTO query_runs(
              run_id, case_id, source_system, query_name, query_text,
              executed_at, time_start, time_end, raw_path, row_count, file_hash, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL)
            """,
            (
                run_id,
                case_id,
                source,
                query_name,
                query_text,
                normalize_ts(executed_at) if executed_at else now_utc_iso(),
                normalize_ts(time_start),
                normalize_ts(time_end),
                str(dest_path.relative_to(paths["case_dir"])),
                file_hash,
            ),
        )
    return run_id


def ingest_run(case_id: str, run_id: str) -> int:
    paths = case_paths(case_id)
    if not paths["db_path"].exists():
        raise FileNotFoundError(f"Case not initialized: {paths['db_path']}")

    with connect(paths["db_path"]) as conn:
        conn.row_factory = sqlite3.Row
        run = conn.execute(
            "SELECT * FROM query_runs WHERE run_id = ? AND case_id = ?",
            (run_id, case_id),
        ).fetchone()
        if not run:
            raise ValueError(f"Unknown run_id: {run_id}")
        raw_path = paths["case_dir"] / run["raw_path"]

        insert_sql = """
            INSERT OR IGNORE INTO events(
              case_id, run_id, event_ts, source_system, source_name, event_type, host, user, src_ip,
              dest_ip, process_name, process_cmdline, process_id, parent_pid,
              parent_process_name, parent_process_cmdline, file_hash, file_path,
              file_name, file_extension, file_size, file_owner, registry_hive,
              registry_key, registry_value, registry_value_name, registry_value_type,
              registry_value_data, dns_query, url, http_method, http_status, bytes_in,
              bytes_out, src_port, dest_port, protocol, event_id, logon_type, session_id,
              user_sid, integrity_level, artifact_type, artifact_path, edr_alert_id,
              tactic, technique, outcome, severity, message, source_event_id, raw_ref,
              raw_json, extras_json, fingerprint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        count = 0
        batch: List[tuple] = []
        extras_batch: List[tuple] = []
        conn.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS event_fields_staging (
              case_id TEXT NOT NULL,
              run_id TEXT NOT NULL,
              raw_ref TEXT NOT NULL,
              field_name TEXT NOT NULL,
              field_value TEXT
            )
            """
        )
        for line_no, row in ingest_lib.iter_rows(raw_path):
            raw_ref = f"{run['raw_path']}#L{line_no}"
            event, extras = ingest_lib.prepare_event(case_id, run_id, raw_ref, row)
            batch.append(event)
            for field_name, field_value in extras.items():
                extras_batch.append((case_id, run_id, raw_ref, field_name, field_value))
            if len(batch) >= 1000:
                conn.executemany(insert_sql, batch)
                count += len(batch)
                batch.clear()
            if len(extras_batch) >= 2000:
                conn.executemany(
                    """
                    INSERT INTO event_fields_staging(case_id, run_id, raw_ref, field_name, field_value)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    extras_batch,
                )
                extras_batch.clear()
        if batch:
            conn.executemany(insert_sql, batch)
            count += len(batch)
        if extras_batch:
            conn.executemany(
                """
                INSERT INTO event_fields_staging(case_id, run_id, raw_ref, field_name, field_value)
                VALUES (?, ?, ?, ?, ?)
                """,
                extras_batch,
            )

        conn.execute(
            """
            INSERT OR IGNORE INTO event_fields(event_pk, case_id, field_name, field_value)
            SELECT e.event_pk, s.case_id, s.field_name, s.field_value
            FROM event_fields_staging s
            JOIN events e
              ON e.case_id = s.case_id
             AND e.run_id = s.run_id
             AND e.raw_ref = s.raw_ref
            """
        )
        conn.execute("DELETE FROM event_fields_staging")

        conn.execute(
            "UPDATE query_runs SET row_count = ?, ingested_at = ? WHERE run_id = ?",
            (count, now_utc_iso(), run_id),
        )
    return count


def ingest_all(case_id: str) -> List[str]:
    paths = case_paths(case_id)
    if not paths["db_path"].exists():
        raise FileNotFoundError(f"Case not initialized: {paths['db_path']}")

    run_ids: List[str] = []
    with connect(paths["db_path"]) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT run_id FROM query_runs WHERE case_id = ? AND ingested_at IS NULL",
            (case_id,),
        ).fetchall()
        run_ids = [row["run_id"] for row in rows]

    for run_id in run_ids:
        ingest_run(case_id, run_id)
    return run_ids


def export_timeline(case_id: str, fmt: str, output_path: Optional[Path]) -> Path:
    import pandas as pd

    paths = case_paths(case_id)
    if not paths["db_path"].exists():
        raise FileNotFoundError(f"Case not initialized: {paths['db_path']}")

    export_dir = paths["exports"]
    export_dir.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = export_dir / f"timeline.{fmt}"

    with connect(paths["db_path"]) as conn:
        df = pd.read_sql_query(
            """
            SELECT
              e.event_ts, e.source_system, e.source_name, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
              e.process_name, e.process_cmdline, e.file_hash, e.outcome, e.severity,
              e.message, e.source_event_id, e.raw_ref, e.raw_json, e.extras_json,
              q.run_id, q.query_name, q.executed_at, q.time_start, q.time_end
            FROM events e
            JOIN query_runs q ON e.run_id = q.run_id
            WHERE e.case_id = ?
            ORDER BY e.event_ts ASC
            """,
            conn,
            params=(case_id,),
        )

    if fmt == "parquet":
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    return output_path
