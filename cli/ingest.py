from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

from cli.utils import compact_json, normalize_ts, sha256_text

REQUIRED_FIELDS = [
    "event_ts",
    "event_type",
    "host",
    "user",
    "src_ip",
    "dest_ip",
    "process_name",
    "process_cmdline",
    "file_hash",
    "outcome",
    "severity",
    "message",
]

EXTENDED_FIELDS = [
    "event_id",
    "logon_type",
    "session_id",
    "user_sid",
    "integrity_level",
    "process_id",
    "parent_pid",
    "parent_process_name",
    "parent_process_cmdline",
    "file_path",
    "file_name",
    "file_extension",
    "file_size",
    "file_owner",
    "registry_hive",
    "registry_key",
    "registry_value",
    "registry_value_name",
    "registry_value_type",
    "registry_value_data",
    "dns_query",
    "url",
    "http_method",
    "http_status",
    "bytes_in",
    "bytes_out",
    "src_port",
    "dest_port",
    "protocol",
    "artifact_type",
    "artifact_path",
    "edr_alert_id",
    "tactic",
    "technique",
]

KNOWN_FIELDS = set(REQUIRED_FIELDS + EXTENDED_FIELDS + [
    "source",
    "source_system",
    "source_name",
    "run_id",
    "query_name",
    "query_text",
    "executed_at",
    "time_start",
    "time_end",
    "source_event_id",
    "raw_json",
    "extras_json",
])


def _normalize_value(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _parse_ndjson(path: Path) -> Iterator[Tuple[int, Dict[str, str]]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            yield line_no, json.loads(line)


def _parse_csv(path: Path) -> Iterator[Tuple[int, Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_no, row in enumerate(reader, start=2):
            yield row_no, row


def iter_rows(path: Path) -> Iterator[Tuple[int, Dict[str, str]]]:
    if path.suffix.lower() == ".csv":
        return _parse_csv(path)
    return _parse_ndjson(path)


def validate_row(row: Dict[str, str]) -> List[str]:
    missing = [field for field in REQUIRED_FIELDS if field not in row]
    if not row.get("source_system") and not row.get("source"):
        missing.append("source_system")
    return missing


def event_fingerprint(row: Dict[str, str]) -> str:
    core = [
        row.get("event_ts") or "",
        row.get("source_system") or row.get("source") or "",
        row.get("event_type") or "",
        row.get("host") or "",
        row.get("user") or "",
        row.get("src_ip") or "",
        row.get("dest_ip") or "",
        row.get("process_name") or "",
        row.get("process_cmdline") or "",
        row.get("file_hash") or "",
        row.get("outcome") or "",
        row.get("severity") or "",
        row.get("message") or "",
    ]
    return sha256_text("|".join(core))


def prepare_event(
    case_id: str,
    run_id: str,
    raw_ref: str,
    row: Dict[str, str],
) -> Tuple[Tuple, Dict[str, str]]:
    normalized = {key: _normalize_value(value) for key, value in row.items()}
    missing = validate_row(normalized)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    raw_json_value = normalized.get("raw_json")
    raw_json = raw_json_value if raw_json_value else None
    extras = {k: v for k, v in normalized.items() if k not in KNOWN_FIELDS}
    extras_json = compact_json(extras) if extras else None

    source_system = normalized.get("source_system") or normalized.get("source")
    source_name = normalized.get("source_name")
    source_event_id = normalized.get("source_event_id")
    fingerprint = None if source_event_id else event_fingerprint(normalized)

    event_tuple = (
        case_id,
        run_id,
        normalize_ts(normalized["event_ts"]),
        source_system,
        source_name,
        normalized["event_type"],
        normalized.get("host"),
        normalized.get("user"),
        normalized.get("src_ip"),
        normalized.get("dest_ip"),
        normalized.get("process_name"),
        normalized.get("process_cmdline"),
        normalized.get("process_id"),
        normalized.get("parent_pid"),
        normalized.get("parent_process_name"),
        normalized.get("parent_process_cmdline"),
        normalized.get("file_hash"),
        normalized.get("file_path"),
        normalized.get("file_name"),
        normalized.get("file_extension"),
        normalized.get("file_size"),
        normalized.get("file_owner"),
        normalized.get("registry_hive"),
        normalized.get("registry_key"),
        normalized.get("registry_value"),
        normalized.get("registry_value_name"),
        normalized.get("registry_value_type"),
        normalized.get("registry_value_data"),
        normalized.get("dns_query"),
        normalized.get("url"),
        normalized.get("http_method"),
        normalized.get("http_status"),
        normalized.get("bytes_in"),
        normalized.get("bytes_out"),
        normalized.get("src_port"),
        normalized.get("dest_port"),
        normalized.get("protocol"),
        normalized.get("event_id"),
        normalized.get("logon_type"),
        normalized.get("session_id"),
        normalized.get("user_sid"),
        normalized.get("integrity_level"),
        normalized.get("artifact_type"),
        normalized.get("artifact_path"),
        normalized.get("edr_alert_id"),
        normalized.get("tactic"),
        normalized.get("technique"),
        normalized.get("outcome"),
        normalized.get("severity"),
        normalized.get("message"),
        source_event_id,
        raw_ref,
        raw_json,
        extras_json,
        fingerprint,
    )
    return event_tuple, extras
