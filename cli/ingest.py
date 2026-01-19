from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

from cli.utils import compact_json, normalize_ts, sha256_text

REQUIRED_FIELDS = [
    "event_ts",
    "source",
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

KNOWN_FIELDS = set(REQUIRED_FIELDS + [
    "run_id",
    "query_name",
    "query_text",
    "executed_at",
    "time_start",
    "time_end",
    "source_event_id",
    "raw_json",
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
    return missing


def event_fingerprint(row: Dict[str, str]) -> str:
    core = [
        row.get("event_ts", ""),
        row.get("source", ""),
        row.get("event_type", ""),
        row.get("host", ""),
        row.get("user", ""),
        row.get("src_ip", ""),
        row.get("dest_ip", ""),
        row.get("process_name", ""),
        row.get("process_cmdline", ""),
        row.get("file_hash", ""),
        row.get("outcome", ""),
        row.get("severity", ""),
        row.get("message", ""),
    ]
    return sha256_text("|".join(core))


def prepare_event(
    case_id: str,
    run_id: str,
    raw_ref: str,
    row: Dict[str, str],
) -> Tuple:
    normalized = {key: _normalize_value(value) for key, value in row.items()}
    missing = validate_row(normalized)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    raw_json_value = normalized.get("raw_json")
    extras = {k: v for k, v in normalized.items() if k not in KNOWN_FIELDS}
    if raw_json_value:
        raw_json = raw_json_value
    elif extras:
        raw_json = compact_json(extras)
    else:
        raw_json = None

    source_event_id = normalized.get("source_event_id")
    fingerprint = None if source_event_id else event_fingerprint(normalized)

    return (
        case_id,
        run_id,
        normalize_ts(normalized["event_ts"]),
        normalized["source"],
        normalized["event_type"],
        normalized.get("host"),
        normalized.get("user"),
        normalized.get("src_ip"),
        normalized.get("dest_ip"),
        normalized.get("process_name"),
        normalized.get("process_cmdline"),
        normalized.get("file_hash"),
        normalized.get("outcome"),
        normalized.get("severity"),
        normalized.get("message"),
        source_event_id,
        raw_ref,
        raw_json,
        fingerprint,
    )
