from __future__ import annotations

from typing import Dict, List, Tuple

from services.db import distinct_values

ENTITY_TYPES = ["host", "user", "ip", "hash", "process"]
ENTITY_COLUMN_MAP = {
    "host": ["host"],
    "user": ["user"],
    "ip": ["src_ip", "dest_ip"],
    "hash": ["file_hash"],
    "process": ["process_name"],
}
RELATED_ENTITY_MAP = {
    "user": [
        ("Hosts", "host", "host"),
        ("Source IPs", "src_ip", "ip"),
        ("Destination IPs", "dest_ip", "ip"),
        ("Processes", "process_name", "process"),
    ],
    "host": [
        ("Users", "user", "user"),
        ("Source IPs", "src_ip", "ip"),
        ("Destination IPs", "dest_ip", "ip"),
        ("Processes", "process_name", "process"),
    ],
    "ip": [
        ("Hosts", "host", "host"),
        ("Users", "user", "user"),
        ("Processes", "process_name", "process"),
    ],
    "process": [
        ("Hosts", "host", "host"),
        ("Users", "user", "user"),
        ("Hashes", "file_hash", "hash"),
    ],
    "hash": [
        ("Hosts", "host", "host"),
        ("Processes", "process_name", "process"),
    ],
}


def entity_where_clause(entity_type: str, entity_value: str) -> Tuple[str, List[str]]:
    if entity_type == "ip":
        return "(e.src_ip = ? OR e.dest_ip = ?)", [entity_value, entity_value]
    column = ENTITY_COLUMN_MAP[entity_type][0]
    return f"e.{column} = ?", [entity_value]


def entity_options(case_id: str, entity_type: str, limit: int = 500) -> List[str]:
    if entity_type == "ip":
        values = distinct_values(case_id, "src_ip", limit) + distinct_values(case_id, "dest_ip", limit)
        return sorted({value for value in values if value})
    column = ENTITY_COLUMN_MAP[entity_type][0]
    return distinct_values(case_id, column, limit)


def load_case_event_type_counts(case_id: str, query_df) -> Dict[str, int]:
    df = query_df(
        case_id,
        """
        SELECT event_type, COUNT(*) AS count
        FROM events
        WHERE case_id = ?
        GROUP BY event_type
        """,
        (case_id,),
    )
    return {row["event_type"]: int(row["count"]) for _, row in df.iterrows()}
