from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import streamlit as st


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

