from __future__ import annotations

from typing import Dict, List, Tuple

import yaml

from api.services.db import distinct_values
from cli.commands import case_paths

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


def load_entity_config(case_id: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """Load entity configuration from case_schema.yaml.

    Returns:
        Tuple of (entity_types, entity_column_map)
        Falls back to hardcoded defaults if no config exists.
    """
    paths = case_paths(case_id)
    schema_path = paths["case_dir"] / "mappers" / "case_schema.yaml"

    if schema_path.exists():
        with schema_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        entity_fields = config.get("entity_fields")
        if entity_fields and isinstance(entity_fields, dict):
            entity_types = list(entity_fields.keys())
            return entity_types, entity_fields

    # Fall back to defaults
    return ENTITY_TYPES, ENTITY_COLUMN_MAP


def entity_where_clause(
    case_id: str, entity_type: str, entity_value: str
) -> Tuple[str, List[str]]:
    """Build SQL WHERE clause for filtering by entity.

    Args:
        case_id: Case identifier for loading entity config
        entity_type: Type of entity (host, user, ip, etc.)
        entity_value: Value to filter by

    Returns:
        Tuple of (where_clause, params)
    """
    _, entity_map = load_entity_config(case_id)
    columns = entity_map.get(entity_type, [])

    if not columns:
        # Fall back to using entity_type as column name
        return f"e.{entity_type} = ?", [entity_value]

    if len(columns) > 1:
        # Multiple columns (e.g., ip -> [src_ip, dest_ip])
        conditions = " OR ".join([f"e.{col} = ?" for col in columns])
        return f"({conditions})", [entity_value] * len(columns)

    return f"e.{columns[0]} = ?", [entity_value]


def entity_options(case_id: str, entity_type: str, limit: int = 500) -> List[str]:
    """Get distinct values for an entity type in a case.

    Args:
        case_id: Case identifier
        entity_type: Type of entity (host, user, ip, etc.)
        limit: Maximum number of values to return

    Returns:
        List of distinct entity values
    """
    _, entity_map = load_entity_config(case_id)
    columns = entity_map.get(entity_type, [])

    if not columns:
        return []

    if len(columns) > 1:
        # Multiple columns - merge distinct values from all
        all_values = []
        for col in columns:
            all_values.extend(distinct_values(case_id, col, limit))
        return sorted({value for value in all_values if value})

    return distinct_values(case_id, columns[0], limit)


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
