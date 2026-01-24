from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import streamlit as st


@dataclass
class FilterPreset:
    """A predefined filter configuration."""
    name: str
    description: str
    filters: Dict[str, Any]


# Quick filter presets for common investigation patterns
FILTER_PRESETS: List[FilterPreset] = [
    FilterPreset(
        name="Failed/Denied Only",
        description="Events with failure or denied outcomes",
        filters={"outcome_contains": ["fail", "denied", "error", "reject"]},
    ),
    FilterPreset(
        name="High Severity",
        description="High and critical severity events",
        filters={"severity_in": ["high", "critical"]},
    ),
    FilterPreset(
        name="Process Activity",
        description="Process creation and execution events",
        filters={"event_type_contains": ["process", "execution", "spawn"]},
    ),
    FilterPreset(
        name="Network Activity",
        description="Network connection and DNS events",
        filters={"event_type_contains": ["network", "connection", "dns", "firewall"]},
    ),
    FilterPreset(
        name="Authentication",
        description="Login and authentication events",
        filters={"event_type_contains": ["auth", "login", "logon", "session"]},
    ),
    FilterPreset(
        name="Registry Changes",
        description="Registry modification events",
        filters={"event_type_contains": ["registry"]},
    ),
]


def get_preset_names() -> List[str]:
    """Get list of preset names for dropdown."""
    return ["Custom..."] + [p.name for p in FILTER_PRESETS]


def get_preset_by_name(name: str) -> Optional[FilterPreset]:
    """Get a preset by name."""
    for p in FILTER_PRESETS:
        if p.name == name:
            return p
    return None


def apply_preset_to_query(
    preset: FilterPreset,
    base_where: str,
    params: List,
) -> Tuple[str, List]:
    """Apply preset filters to a query."""
    clauses = [base_where]

    if "outcome_contains" in preset.filters:
        patterns = preset.filters["outcome_contains"]
        or_clauses = []
        for pattern in patterns:
            or_clauses.append("LOWER(e.outcome) LIKE ?")
            params.append(f"%{pattern}%")
        if or_clauses:
            clauses.append(f"({' OR '.join(or_clauses)})")

    if "severity_in" in preset.filters:
        severities = preset.filters["severity_in"]
        placeholders = ", ".join(["?"] * len(severities))
        clauses.append(f"LOWER(e.severity) IN ({placeholders})")
        params.extend([s.lower() for s in severities])

    if "event_type_contains" in preset.filters:
        patterns = preset.filters["event_type_contains"]
        or_clauses = []
        for pattern in patterns:
            or_clauses.append("LOWER(e.event_type) LIKE ?")
            params.append(f"%{pattern}%")
        if or_clauses:
            clauses.append(f"({' OR '.join(or_clauses)})")

    return " AND ".join(clauses), params


def build_filters(
    case_id: str,
    start_dt: datetime,
    end_dt: datetime,
    sources: List[str],
    event_types: List[str],
    hosts: List[str],
    users: List[str],
    ips: List[str],
    processes: List[str],
    hashes: List[str],
) -> Tuple[str, List]:
    clauses = ["e.case_id = ?"]
    params: List = [case_id]
    clauses.append("e.event_ts BETWEEN ? AND ?")
    params.extend([
        start_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        end_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    ])

    def add_in_filter(values: List[str], column: str) -> None:
        if values:
            placeholders = ", ".join(["?"] * len(values))
            clauses.append(f"e.{column} IN ({placeholders})")
            params.extend(values)

    add_in_filter(sources, "source_system")
    add_in_filter(event_types, "event_type")
    add_in_filter(hosts, "host")
    add_in_filter(users, "user")
    add_in_filter(processes, "process_name")
    add_in_filter(hashes, "file_hash")

    if ips:
        placeholders = ", ".join(["?"] * len(ips))
        clauses.append(f"(e.src_ip IN ({placeholders}) OR e.dest_ip IN ({placeholders}))")
        params.extend(ips)
        params.extend(ips)

    return " AND ".join(clauses), params


def time_range_selector(min_ts: datetime, max_ts: datetime) -> Tuple[datetime, datetime]:
    mode = st.selectbox("Time Range", ["Full case", "Last 24h", "Last 72h", "Custom"])
    if mode == "Full case":
        return min_ts, max_ts
    if mode == "Last 24h":
        end_dt = max_ts
        start_dt = max_ts - timedelta(hours=24)
        return start_dt, end_dt
    if mode == "Last 72h":
        end_dt = max_ts
        start_dt = max_ts - timedelta(hours=72)
        return start_dt, end_dt

    start_date, end_date = st.date_input(
        "Custom range",
        value=(min_ts.date(), max_ts.date()),
        min_value=min_ts.date(),
        max_value=max_ts.date(),
        key="swimlane_date_range",
    )
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
    return start_dt, end_dt

