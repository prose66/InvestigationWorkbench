from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from cli import ingest as ingest_lib
from cli.db import connect, init_db
from cli.mappers import get_mapper
from cli.utils import now_utc_iso, normalize_ts, sha256_file

ROOT_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT_DIR / "cases"
SCHEMA_PATH = ROOT_DIR / "cli" / "schema.sql"


@dataclass
class IngestResult:
    """Result of an ingestion run with enhanced feedback."""
    run_id: str
    events_ingested: int
    events_skipped: int
    source: str = ""
    mapper_type: str = "generic"  # "yaml_case", "yaml_builtin", "builtin", "generic"
    fields_mapped: Dict[str, str] = field(default_factory=dict)
    fields_unmapped: List[str] = field(default_factory=list)
    errors: List[dict] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.events_ingested > 0 or self.events_skipped == 0

    def generate_suggestions(self, case_id: str):
        """Generate helpful suggestions based on errors."""
        if not self.errors:
            return

        first_error = self.errors[0].get("error", "") if self.errors else ""

        if "event_ts" in first_error or "Missing required fields" in first_error:
            self.suggestions.append(
                f"Create cases/{case_id}/mappers/{self.source}.yaml to map your timestamp field to event_ts"
            )

        if len(self.fields_unmapped) > 5:
            self.suggestions.append(
                f"Many unmapped fields ({len(self.fields_unmapped)}) went to extras_json. "
                f"Consider creating a custom mapper for better field mapping."
            )

        if self.mapper_type == "generic" and self.events_skipped > 0:
            self.suggestions.append(
                f"Using generic mapper. Create a YAML config for source '{self.source}' "
                f"to improve field mapping."
            )


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
    allow_duplicate: bool = False,
) -> str:
    """Add a query run to a case.
    
    Args:
        case_id: Case identifier
        source: Source system (splunk, kusto, etc.)
        query_name: Human-readable query name
        query_text: Optional query text
        time_start: Query time range start (ISO8601)
        time_end: Query time range end (ISO8601)
        file_path: Path to the export file
        executed_at: When the query was executed (ISO8601)
        allow_duplicate: If False, raise error if file already added
        
    Returns:
        The new run_id
        
    Raises:
        FileNotFoundError: If case not initialized
        ValueError: If file is a duplicate and allow_duplicate=False
    """
    paths = case_paths(case_id)
    if not paths["db_path"].exists():
        raise FileNotFoundError(f"Case not initialized: {paths['db_path']}")

    # Check for duplicate file
    file_hash = sha256_file(file_path)
    with connect(paths["db_path"]) as conn:
        existing = conn.execute(
            "SELECT run_id, query_name FROM query_runs WHERE case_id = ? AND file_hash = ?",
            (case_id, file_hash),
        ).fetchone()
        if existing and not allow_duplicate:
            raise ValueError(
                f"Duplicate file detected. Already added as run {existing[0]} "
                f"(query: {existing[1]}). Use --allow-duplicate to override."
            )

    run_id = str(uuid.uuid4())
    raw_dir = paths["raw_base"] / source
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest_path = raw_dir / f"{run_id}{file_path.suffix.lower()}"
    shutil.copy2(file_path, dest_path)

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


def ingest_run(
    case_id: str,
    run_id: str,
    skip_errors: bool = False,
    lenient: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> IngestResult:
    """Ingest events from a query run into the database.

    Args:
        case_id: Case identifier
        run_id: Query run identifier
        skip_errors: If True, skip malformed rows instead of aborting
        lenient: If True, only require event_ts and event_type
        progress_callback: Optional callback(processed, total) for progress updates

    Returns:
        IngestResult with counts, errors, and mapping feedback
    """
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
        source_system = run["source_system"]

        # Get appropriate mapper for this source (with case-specific config support)
        mapper, mapper_type = get_mapper(source_system, paths["case_dir"])

        # Initialize result with enhanced feedback
        result = IngestResult(
            run_id=run_id,
            events_ingested=0,
            events_skipped=0,
            source=source_system,
            mapper_type=mapper_type,
        )

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
        
        processed = 0
        first_row = True
        for line_no, row in ingest_lib.iter_rows(raw_path):
            raw_ref = f"{run['raw_path']}#L{line_no}"
            processed += 1

            # Track field mapping stats on first row
            if first_row:
                source_keys_lower = {k.lower() for k in row.keys()}

                # Which source fields matched mapper definitions
                result.fields_mapped = {
                    src: mapper.field_map[src]
                    for src in mapper.field_map
                    if src.lower() in source_keys_lower
                }

                # Which source fields had no mapping (will go to extras_json)
                mapped_source_fields = {k.lower() for k in mapper.field_map.keys()}
                result.fields_unmapped = [
                    k for k in row.keys()
                    if k.lower() not in mapped_source_fields
                    and k.lower() not in ingest_lib.KNOWN_FIELDS
                ]
                first_row = False

            try:
                event, extras = ingest_lib.prepare_event(
                    case_id, run_id, raw_ref, row,
                    mapper=mapper,
                    lenient=lenient,
                )
                batch.append(event)
                for field_name, field_value in extras.items():
                    extras_batch.append((case_id, run_id, raw_ref, field_name, field_value))
            except Exception as exc:
                if skip_errors:
                    result.events_skipped += 1
                    result.errors.append({
                        "line": line_no,
                        "error": str(exc),
                        "raw_ref": raw_ref,
                        "sample": {k: v for k, v in list(row.items())[:5]},
                    })
                    continue
                else:
                    raise
            
            if len(batch) >= 1000:
                conn.executemany(insert_sql, batch)
                result.events_ingested += len(batch)
                batch.clear()
                if progress_callback:
                    progress_callback(processed, 0)
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
            result.events_ingested += len(batch)
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
            (result.events_ingested, now_utc_iso(), run_id),
        )
        
        # Write errors to file if any
        if result.errors:
            error_path = paths["case_dir"] / "raw" / source_system / f"{run_id}_errors.ndjson"
            with error_path.open("w", encoding="utf-8") as f:
                for err in result.errors:
                    f.write(json.dumps(err) + "\n")

    # Generate helpful suggestions
    result.generate_suggestions(case_id)

    return result


def ingest_all(
    case_id: str,
    skip_errors: bool = False,
    lenient: bool = False,
) -> List[IngestResult]:
    """Ingest all pending query runs for a case.
    
    Args:
        case_id: Case identifier
        skip_errors: If True, skip malformed rows instead of aborting
        lenient: If True, only require event_ts and event_type
        
    Returns:
        List of IngestResult for each run
    """
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

    results = []
    for run_id in run_ids:
        result = ingest_run(case_id, run_id, skip_errors=skip_errors, lenient=lenient)
        results.append(result)
    return results


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


def print_ingest_report(result: IngestResult, verbose: bool = False) -> List[str]:
    """Format an IngestResult for CLI output.

    Args:
        result: The IngestResult to format
        verbose: If True, show more detail

    Returns:
        List of formatted output lines
    """
    lines = []
    source_label = f"{result.source} ({result.mapper_type})"
    lines.append(f"\nIngesting {source_label}")

    if result.fields_mapped:
        mapped_str = ", ".join(
            f"{k}->{v}" for k, v in list(result.fields_mapped.items())[:8]
        )
        if len(result.fields_mapped) > 8:
            mapped_str += f" (+{len(result.fields_mapped) - 8} more)"
        lines.append(f"  [mapped] {mapped_str}")

    if result.fields_unmapped:
        unmapped_str = ", ".join(result.fields_unmapped[:10])
        if len(result.fields_unmapped) > 10:
            unmapped_str += f" (+{len(result.fields_unmapped) - 10} more)"
        lines.append(f"  [unmapped -> extras_json] {unmapped_str}")

    lines.append(f"  Ingested: {result.events_ingested} events")

    if result.events_skipped > 0:
        lines.append(f"  Skipped: {result.events_skipped} rows")
        if result.errors and verbose:
            err = result.errors[0]
            lines.append(f"    Line {err['line']}: {err['error']}")

    for suggestion in result.suggestions:
        lines.append(f"\n  Tip: {suggestion}")

    return lines


def preview(
    case_id: str,
    source: str,
    file_path: Path,
    limit: int = 5,
) -> Dict:
    """Preview how a file would be ingested without committing.

    Args:
        case_id: Case identifier (for case-specific mappers)
        source: Source system name
        file_path: Path to the file to preview
        limit: Number of rows to preview

    Returns:
        Dict with mapper info and preview rows
    """
    paths = case_paths(case_id)
    case_dir = paths["case_dir"] if paths["case_dir"].exists() else None

    # Get mapper with type info
    mapper, mapper_type = get_mapper(source, case_dir)

    result = {
        "source": source,
        "file": str(file_path),
        "mapper_type": mapper_type,
        "mapper_class": type(mapper).__name__,
        "field_map": mapper.field_map,
        "rows": [],
        "errors": [],
        "fields_in_source": [],
        "fields_mapped": {},
        "fields_unmapped": [],
    }

    # Read and process limited rows
    count = 0
    for line_no, row in ingest_lib.iter_rows(file_path):
        if count >= limit:
            break

        # Track source fields on first row
        if count == 0:
            result["fields_in_source"] = list(row.keys())
            source_keys_lower = {k.lower() for k in row.keys()}

            result["fields_mapped"] = {
                src: mapper.field_map[src]
                for src in mapper.field_map
                if src.lower() in source_keys_lower
            }

            mapped_source_fields = {k.lower() for k in mapper.field_map.keys()}
            result["fields_unmapped"] = [
                k for k in row.keys()
                if k.lower() not in mapped_source_fields
            ]

        try:
            mapped = mapper.map_row(row)
            # Extract key fields for preview
            preview_row = {
                "event_ts": mapped.get("event_ts", ""),
                "event_type": mapped.get("event_type", ""),
                "host": mapped.get("host", ""),
                "user": mapped.get("user", ""),
                "src_ip": mapped.get("src_ip", ""),
                "message": (mapped.get("message") or "")[:50],
            }
            result["rows"].append(preview_row)
        except Exception as e:
            result["errors"].append({
                "line": line_no,
                "error": str(e),
            })

        count += 1

    return result


def print_preview(preview_result: Dict) -> List[str]:
    """Format preview result for CLI output.

    Args:
        preview_result: Result from preview()

    Returns:
        List of formatted output lines
    """
    lines = []
    lines.append(f"\nPreview: {Path(preview_result['file']).name}")
    lines.append(f"Mapper: {preview_result['mapper_class']} ({preview_result['mapper_type']})")

    if preview_result["fields_mapped"]:
        mapped_str = ", ".join(
            f"{k}->{v}" for k, v in list(preview_result["fields_mapped"].items())[:6]
        )
        lines.append(f"\nMapped fields: {mapped_str}")

    if preview_result["fields_unmapped"]:
        unmapped_str = ", ".join(preview_result["fields_unmapped"][:8])
        lines.append(f"Unmapped fields: {unmapped_str}")

    # Table header
    lines.append("")
    cols = ["event_ts", "event_type", "host", "user", "src_ip", "message"]
    widths = [20, 14, 12, 12, 15, 30]
    header = " | ".join(col.ljust(w) for col, w in zip(cols, widths))
    lines.append(header)
    lines.append("-" * len(header))

    # Table rows
    for row in preview_result["rows"]:
        row_str = " | ".join(
            str(row.get(col, ""))[:w].ljust(w)
            for col, w in zip(cols, widths)
        )
        lines.append(row_str)

    # Errors
    for err in preview_result["errors"]:
        lines.append(f"[ERROR] Line {err['line']}: {err['error']}")

    return lines
