from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import altair as alt
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT_DIR / "cases"

FEATURE_ENTITY_EXPLORER = False

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

st.set_page_config(page_title="Investigation Workbench", layout="wide")


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


def table_exists(case_id: str, table_name: str) -> bool:
    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?"
    row = query_one(case_id, sql, (table_name,))
    return bool(row)


def entity_options(case_id: str, entity_type: str, limit: int = 500) -> List[str]:
    if entity_type == "ip":
        values = distinct_values(case_id, "src_ip", limit) + distinct_values(case_id, "dest_ip", limit)
        return sorted({value for value in values if value})
    column = ENTITY_COLUMN_MAP[entity_type][0]
    return distinct_values(case_id, column, limit)


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


def entity_where_clause(entity_type: str, entity_value: str) -> Tuple[str, List[str]]:
    if entity_type == "ip":
        return "(e.src_ip = ? OR e.dest_ip = ?)", [entity_value, entity_value]
    column = ENTITY_COLUMN_MAP[entity_type][0]
    return f"e.{column} = ?", [entity_value]


def set_timeline_pivot(entity_type: str, entity_value: str) -> None:
    column_map = {
        "host": "host",
        "user": "user",
        "ip": "src_ip",
        "hash": "file_hash",
        "process": "process_name",
    }
    column = column_map.get(entity_type)
    if column:
        st.session_state["timeline_pivot"] = {"column": column, "value": entity_value}


def queue_page_navigation(page_name: str) -> None:
    st.session_state["next_page"] = page_name


def queue_entity_navigation(entity_type: str, entity_value: str) -> None:
    st.session_state["active_entity"] = {"type": entity_type, "value": entity_value}
    queue_page_navigation("Entity Page")


def queue_timeline_pivot(entity_type: str, entity_value: str) -> None:
    set_timeline_pivot(entity_type, entity_value)
    queue_page_navigation("Timeline Explorer")


def timeline_bucket_format(start_dt: datetime, end_dt: datetime) -> Tuple[str, str]:
    delta = end_dt - start_dt
    if delta > timedelta(days=30):
        return "%Y-%m-%d", "day"
    if delta > timedelta(days=2):
        return "%Y-%m-%d %H:00:00", "hour"
    return "%Y-%m-%d %H:%M:00", "minute"


def swimlane_bucket_size(start_dt: datetime, end_dt: datetime) -> Tuple[str, timedelta]:
    delta = end_dt - start_dt
    if delta <= timedelta(hours=6):
        return "%Y-%m-%d %H:%M:00", timedelta(minutes=5)
    if delta <= timedelta(hours=48):
        return "%Y-%m-%d %H:%M:00", timedelta(minutes=30)
    if delta <= timedelta(days=7):
        return "%Y-%m-%d %H:00:00", timedelta(hours=1)
    return "%Y-%m-%d", timedelta(days=1)


def lane_column(lane_dim: str) -> str:
    return {
        "event_type": "event_type",
        "source_system": "source_system",
        "host": "host",
        "user": "user",
    }[lane_dim]


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


def page_case_overview(case_id: str) -> None:
    st.subheader("Case Overview")
    summary = query_one(
        case_id,
        """
        SELECT COUNT(*) AS total_events,
               COUNT(DISTINCT run_id) AS total_runs
        FROM events
        WHERE case_id = ?
        """,
        (case_id,),
    )

    col1, col2 = st.columns(2)
    col1.metric("Events", summary["total_events"] if summary else 0)
    col2.metric("Runs", summary["total_runs"] if summary else 0)

    min_ts, max_ts = time_bounds(case_id)
    if min_ts and max_ts:
        st.caption(f"Time coverage: {min_ts} to {max_ts} (UTC)")
    else:
        st.info("No events ingested yet.")
        return

    st.markdown("### Counts by Source")
    source_df = query_df(
        case_id,
        "SELECT source_system, COUNT(*) AS count FROM events WHERE case_id = ? GROUP BY source_system",
        (case_id,),
    )
    if not source_df.empty:
        chart = alt.Chart(source_df).mark_bar().encode(
            x=alt.X("source_system:N", title="Source System"),
            y=alt.Y("count:Q", title="Events"),
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("### Counts by Event Type")
    type_df = query_df(
        case_id,
        """
        SELECT event_type, COUNT(*) AS count
        FROM events
        WHERE case_id = ?
        GROUP BY event_type
        ORDER BY count DESC
        """,
        (case_id,),
    )
    st.dataframe(type_df, use_container_width=True)

    st.markdown("### Query Run Coverage")
    runs_df = query_df(
        case_id,
        """
        SELECT run_id, source_system, query_name, executed_at, time_start, time_end, row_count
        FROM query_runs
        WHERE case_id = ?
        ORDER BY executed_at DESC
        """,
        (case_id,),
    )
    st.dataframe(runs_df, use_container_width=True)


def page_timeline(case_id: str) -> None:
    st.subheader("Timeline Explorer")
    min_ts, max_ts = time_bounds(case_id)
    if not min_ts or not max_ts:
        st.info("No events ingested yet.")
        return

    pivot = st.session_state.get("timeline_pivot")
    if pivot:
        st.info(f"Pivot active: {pivot['column']} = {pivot['value']}")

    sources = distinct_values(case_id, "source_system")
    event_types = distinct_values(case_id, "event_type")
    hosts = distinct_values(case_id, "host")
    users = distinct_values(case_id, "user")
    ips = sorted(set(distinct_values(case_id, "src_ip") + distinct_values(case_id, "dest_ip")))
    processes = distinct_values(case_id, "process_name")
    hashes = distinct_values(case_id, "file_hash")

    start_date, end_date = st.date_input(
        "Time range",
        value=(min_ts.date(), max_ts.date()),
        min_value=min_ts.date(),
        max_value=max_ts.date(),
    )
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

    default_hosts = [pivot["value"]] if pivot and pivot["column"] == "host" else []
    default_users = [pivot["value"]] if pivot and pivot["column"] == "user" else []
    default_ips = [pivot["value"]] if pivot and pivot["column"] in ("src_ip", "dest_ip") else []
    default_processes = [pivot["value"]] if pivot and pivot["column"] == "process_name" else []
    default_hashes = [pivot["value"]] if pivot and pivot["column"] == "file_hash" else []

    col1, col2, col3 = st.columns(3)
    selected_sources = col1.multiselect("Source System", sources, default=[])
    selected_event_types = col2.multiselect("Event Type", event_types, default=[])
    selected_hosts = col3.multiselect("Host", hosts, default=default_hosts)

    col4, col5 = st.columns(2)
    selected_users = col4.multiselect("User", users, default=default_users)
    selected_ips = col5.multiselect("IP (src or dest)", ips, default=default_ips)

    col6, col7 = st.columns(2)
    selected_processes = col6.multiselect("Process", processes, default=default_processes)
    selected_hashes = col7.multiselect("File Hash", hashes, default=default_hashes)

    where_clause, params = build_filters(
        case_id,
        start_dt,
        end_dt,
        selected_sources,
        selected_event_types,
        selected_hosts,
        selected_users,
        selected_ips,
        selected_processes,
        selected_hashes,
    )

    bucket_fmt, bucket_label = timeline_bucket_format(start_dt, end_dt)
    timeline_df = query_df(
        case_id,
        f"""
        SELECT strftime('{bucket_fmt}', event_ts) AS bucket, COUNT(*) AS count
        FROM events e
        WHERE {where_clause}
        GROUP BY bucket
        ORDER BY bucket
        """,
        tuple(params),
    )
    if not timeline_df.empty:
        chart = alt.Chart(timeline_df).mark_line(point=True).encode(
            x=alt.X("bucket:T", title=f"Time ({bucket_label})"),
            y=alt.Y("count:Q", title="Events"),
            tooltip=["bucket:T", "count:Q"],
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No events match the selected filters.")

    page_size = st.selectbox("Rows per page", [25, 50, 100], index=1)
    page = st.number_input("Page", min_value=1, value=1, step=1)
    offset = (page - 1) * page_size

    events_df = query_df(
        case_id,
        f"""
        SELECT
          e.event_pk, e.event_ts, e.source_system, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
          e.process_name, e.outcome, e.severity, e.message,
          e.source_event_id, e.raw_ref, e.raw_json,
          q.run_id, q.query_name, q.executed_at, q.time_start, q.time_end
        FROM events e
        JOIN query_runs q ON e.run_id = q.run_id
        WHERE {where_clause}
        ORDER BY e.event_ts ASC
        LIMIT ? OFFSET ?
        """,
        tuple(params + [page_size, offset]),
    )

    st.dataframe(
        events_df[
            [
                "event_ts",
                "source_system",
                "event_type",
                "host",
                "user",
                "src_ip",
                "dest_ip",
                "process_name",
                "outcome",
                "severity",
                "message",
            ]
        ],
        use_container_width=True,
    )

    if not events_df.empty:
        selected_pk = st.selectbox(
            "Select an event for provenance",
            events_df["event_pk"].tolist(),
        )
        selected = events_df[events_df["event_pk"] == selected_pk].iloc[0].to_dict()
        st.markdown("#### Event Provenance")
        st.write(
            {
                "run_id": selected["run_id"],
                "query_name": selected["query_name"],
                "executed_at": selected["executed_at"],
                "time_start": selected["time_start"],
                "time_end": selected["time_end"],
                "raw_ref": selected["raw_ref"],
                "source_event_id": selected["source_event_id"],
            }
        )
        if selected.get("raw_json"):
            st.markdown("#### Raw JSON")
            st.json(selected["raw_json"])


def page_entity_explorer(case_id: str) -> None:
    st.subheader("Entity Explorer")
    entity_type = st.selectbox("Entity type", ["host", "user", "src_ip", "dest_ip", "file_hash"])
    entity_value = st.text_input("Entity value")

    if not entity_value:
        st.info("Enter a value to search.")
        return

    row = query_one(
        case_id,
        f"""
        SELECT MIN(event_ts) AS first_seen, MAX(event_ts) AS last_seen, COUNT(*) AS total_events
        FROM events
        WHERE case_id = ? AND {entity_type} = ?
        """,
        (case_id, entity_value),
    )

    if not row or row["total_events"] == 0:
        st.warning("No events found for that entity.")
        return

    st.write(
        {
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "total_events": row["total_events"],
        }
    )

    counts_df = query_df(
        case_id,
        f"""
        SELECT event_type, COUNT(*) AS count
        FROM events
        WHERE case_id = ? AND {entity_type} = ?
        GROUP BY event_type
        ORDER BY count DESC
        """,
        (case_id, entity_value),
    )
    st.dataframe(counts_df, use_container_width=True)

    recent_df = query_df(
        case_id,
        f"""
        SELECT event_ts, source_system, event_type, host, user, src_ip, dest_ip, process_name, outcome, severity, message
        FROM events
        WHERE case_id = ? AND {entity_type} = ?
        ORDER BY event_ts DESC
        LIMIT 50
        """,
        (case_id, entity_value),
    )
    st.markdown("### Recent Events")
    st.dataframe(recent_df, use_container_width=True)

    if st.button("Pivot to Timeline"):
        st.session_state["timeline_pivot"] = {"column": entity_type, "value": entity_value}
        st.success("Pivot set. Open Timeline Explorer to apply the filter.")


def page_swimlane_timeline(case_id: str) -> None:
    st.subheader("Swimlane Timeline")
    min_ts, max_ts = time_bounds(case_id)
    if not min_ts or not max_ts:
        st.info("No events ingested yet.")
        return

    with st.sidebar:
        st.markdown("### Swimlane Controls")
        start_dt, end_dt = time_range_selector(min_ts, max_ts)
        lane_dim = st.selectbox("Lane Dimension", ["event_type", "source_system", "host", "user"])
        aggregate = st.toggle("Aggregate events", value=True)
        max_lanes = st.slider("Limit lanes to top N", min_value=5, max_value=30, value=15)
        color_by = st.selectbox("Color by", ["event_type", "source_system"])

        st.markdown("#### Filters")
        sources = distinct_values(case_id, "source_system")
        event_types = distinct_values(case_id, "event_type")
        hosts = distinct_values(case_id, "host")
        users = distinct_values(case_id, "user")
        selected_sources = st.multiselect("Source System", sources, default=[])
        selected_event_types = st.multiselect("Event Type", event_types, default=[])
        selected_hosts = st.multiselect("Host", hosts, default=[])
        selected_users = st.multiselect("User", users, default=[])

    where_clause, params = build_filters(
        case_id,
        start_dt,
        end_dt,
        selected_sources,
        selected_event_types,
        selected_hosts,
        selected_users,
        [],
        [],
        [],
    )

    lane_field = lane_column(lane_dim)
    lane_df = query_df(
        case_id,
        f"""
        SELECT e.{lane_field} AS lane, COUNT(*) AS count
        FROM events e
        WHERE {where_clause}
          AND e.{lane_field} IS NOT NULL
          AND e.{lane_field} != ''
        GROUP BY e.{lane_field}
        ORDER BY count DESC
        LIMIT ?
        """,
        tuple(params + [max_lanes]),
    )
    lanes = lane_df["lane"].dropna().tolist()
    if not lanes:
        st.warning("No lanes found for the selected filters.")
        return

    placeholders = ", ".join(["?"] * len(lanes))
    lane_filter = f"e.{lane_field} IN ({placeholders})"
    base_where = f"{where_clause} AND {lane_filter}"
    base_params = params + lanes

    selection_fields = ["lane", "bucket_start"] if aggregate else ["lane", "event_ts"]
    selection = alt.selection_point(fields=selection_fields, name="swimlane_select")

    if aggregate:
        bucket_fmt, bucket_step = swimlane_bucket_size(start_dt, end_dt)
        agg_df = query_df(
            case_id,
            f"""
            SELECT
              e.{lane_field} AS lane,
              strftime('{bucket_fmt}', e.event_ts) AS bucket,
              e.event_type,
              e.source_system,
              COUNT(*) AS count
            FROM events e
            WHERE {base_where}
            GROUP BY lane, bucket, e.event_type, e.source_system
            """,
            tuple(base_params),
        )
        if agg_df.empty:
            st.warning("No events available for this view.")
            return

        agg_df["bucket_start"] = pd.to_datetime(agg_df["bucket"], utc=True)
        agg_df["bucket_end"] = agg_df["bucket_start"] + bucket_step
        grouped = (
            agg_df.groupby(["lane", "bucket_start", "bucket_end"], as_index=False)
            .agg(
                count=("count", "sum"),
                top_event_types=("event_type", lambda x: ", ".join(x.value_counts().head(3).index)),
                sources=("source_system", lambda x: ", ".join(x.value_counts().head(3).index)),
            )
        )
        color_field = "top_event_types" if color_by == "event_type" else "sources"
        grouped["color_key"] = grouped[color_field]
        chart = (
            alt.Chart(grouped)
            .mark_bar()
            .encode(
                x=alt.X("bucket_start:T", title="Time"),
                x2="bucket_end:T",
                y=alt.Y("lane:N", title=lane_dim),
                color=alt.Color("color_key:N", legend=None),
                tooltip=["lane:N", "bucket_start:T", "count:Q", "top_event_types:N", "sources:N"],
            )
            .add_params(selection)
        )
    else:
        events_df = query_df(
            case_id,
            f"""
            SELECT e.event_ts, e.{lane_field} AS lane, e.event_type, e.source_system
            FROM events e
            WHERE {base_where}
            ORDER BY e.event_ts ASC
            LIMIT 5000
            """,
            tuple(base_params),
        )
        if events_df.empty:
            st.warning("No events available for this view.")
            return
        chart = (
            alt.Chart(events_df)
            .mark_tick(thickness=2, opacity=0.6)
            .encode(
                x=alt.X("event_ts:T", title="Time"),
                y=alt.Y("lane:N", title=lane_dim),
                color=alt.Color(f"{color_by}:N", legend=None),
                tooltip=["lane:N", "event_ts:T", "event_type:N", "source_system:N"],
            )
            .add_params(selection)
        )

    chart_state = st.altair_chart(
        chart,
        use_container_width=True,
        on_select="rerun",
        selection_mode="swimlane_select",
    )

    selected_lane = None
    selected_time_start = None
    selected_time_end = None
    selection_data = getattr(chart_state, "selection", None) or {}
    selected = selection_data.get("swimlane_select")
    if isinstance(selected, dict):
        selected_lane = selected.get("lane")
        if aggregate and selected.get("bucket_start"):
            selected_time_start = pd.to_datetime(selected["bucket_start"], utc=True)
            selected_time_end = selected_time_start + bucket_step
        elif not aggregate and selected.get("event_ts"):
            selected_time_start = pd.to_datetime(selected["event_ts"], utc=True) - timedelta(minutes=30)
            selected_time_end = pd.to_datetime(selected["event_ts"], utc=True) + timedelta(minutes=30)

    if st.button("Clear selection"):
        selected_lane = None
        selected_time_start = None
        selected_time_end = None

    if selected_lane or selected_time_start:
        st.info(
            "Selection active"
            + (f": lane={selected_lane}" if selected_lane else "")
            + (f", time={selected_time_start} to {selected_time_end}" if selected_time_start else "")
        )

    if lane_dim in ("host", "user"):
        st.markdown("#### Pivot Lanes")
        for lane_value in lanes:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(lane_value)
            with col2:
                if st.button("Open Entity", key=f"lane-entity-{lane_value}"):
                    queue_entity_navigation(lane_dim, lane_value)
                    st.rerun()

    st.markdown("#### Events in View")
    extra_clauses = []
    extra_params: List[str] = []
    if selected_lane:
        extra_clauses.append(f"e.{lane_field} = ?")
        extra_params.append(selected_lane)
    if selected_time_start and selected_time_end:
        extra_clauses.append("e.event_ts BETWEEN ? AND ?")
        extra_params.extend([
            selected_time_start.isoformat().replace("+00:00", "Z"),
            selected_time_end.isoformat().replace("+00:00", "Z"),
        ])
    extra_where = f" AND {' AND '.join(extra_clauses)}" if extra_clauses else ""
    visible_df = query_df(
        case_id,
        f"""
        SELECT e.event_pk, e.event_ts, e.source_system, e.event_type, e.host, e.user, e.message,
               e.raw_json, e.raw_ref, e.run_id
        FROM events e
        WHERE {base_where}{extra_where}
        ORDER BY e.event_ts ASC
        LIMIT 500
        """,
        tuple(base_params + extra_params),
    )
    if visible_df.empty:
        st.caption("No events in view.")
        return

        st.dataframe(
            visible_df[
                ["event_ts", "source_system", "event_type", "host", "user", "message"]
            ],
            use_container_width=True,
        )

    selected_pk = st.selectbox("Inspect event", visible_df["event_pk"].tolist())
    selected = visible_df[visible_df["event_pk"] == selected_pk].iloc[0].to_dict()
    st.markdown("#### Event Provenance")
    st.write({"run_id": selected["run_id"], "source_system": selected["source_system"]})
    if selected.get("raw_json"):
        st.markdown("#### Raw JSON")
        st.json(selected["raw_json"])
    else:
        st.write({"raw_ref": selected.get("raw_ref")})


def load_case_event_type_counts(case_id: str) -> Dict[str, int]:
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


def score_event(
    event: dict,
    event_type_counts: Dict[str, int],
    last_seen: Optional[datetime],
    window_start: Optional[datetime],
) -> int:
    score = 0
    severity = (event.get("severity") or "").lower()
    outcome = (event.get("outcome") or "").lower()
    event_type = (event.get("event_type") or "").lower()

    if severity in ("high", "critical"):
        score += 2
    if "fail" in outcome or outcome in ("failure", "denied", "error"):
        score += 2
    if any(token in event_type for token in ("process", "privilege", "admin", "suspicious")):
        score += 2

    count = event_type_counts.get(event.get("event_type") or "", 0)
    if count and count <= 5:
        score += 1

    if last_seen and window_start and event.get("event_ts"):
        try:
            event_ts = datetime.fromisoformat(event["event_ts"].replace("Z", "+00:00"))
            total = (last_seen - window_start).total_seconds()
            if total > 0:
                threshold = window_start + timedelta(seconds=total * 0.9)
                if event_ts >= threshold:
                    score += 1
        except ValueError:
            pass

    return score


def render_related_entities(
    case_id: str,
    title: str,
    related_field: str,
    target_type: str,
    base_where: str,
    base_params: List[str],
    limit: int = 15,
) -> None:
    related_df = query_df(
        case_id,
        f"""
        SELECT
          e.{related_field} AS value,
          COUNT(*) AS count,
          MIN(e.event_ts) AS first_seen,
          MAX(e.event_ts) AS last_seen
        FROM events e
        WHERE {base_where}
          AND e.{related_field} IS NOT NULL
          AND e.{related_field} != ''
        GROUP BY e.{related_field}
        ORDER BY count DESC
        LIMIT ?
        """,
        tuple(base_params + [limit]),
    )

    st.markdown(f"#### {title}")
    if related_df.empty:
        st.caption("No related entities found.")
        return

    for _, row in related_df.iterrows():
        value = row["value"]
        count = int(row["count"])
        first_seen = row["first_seen"]
        last_seen = row["last_seen"]
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.button(
                f"{value} ({count})",
                key=f"entity-{title}-{value}",
                on_click=queue_entity_navigation,
                args=(target_type, value),
            )
        with col2:
            st.button(
                "Pivot",
                key=f"pivot-{title}-{value}",
                on_click=queue_timeline_pivot,
                args=(target_type, value),
            )
        with col3:
            st.caption(f"{first_seen} -> {last_seen}")


def page_entity_page(case_id: str) -> None:
    st.subheader("Entity Page")
    with st.sidebar:
        st.markdown("### Entity")
        entity_type = st.selectbox("Entity Type", ENTITY_TYPES, key="entity_type_input")
        entity_value = st.text_input("Entity Value", key="entity_value_input").strip()
        entity_list = entity_options(case_id, entity_type)
        entity_select = st.selectbox(
            "Select from ingested entities",
            [""] + entity_list,
            key="entity_value_select",
        )
        if entity_select:
            entity_value = entity_select
        open_entity = st.button("Open Entity")
        pivot_to_timeline = st.button("Pivot to Timeline")

    if open_entity and entity_value:
        st.session_state["active_entity"] = {"type": entity_type, "value": entity_value}

    active_entity = st.session_state.get("active_entity")
    if not active_entity and entity_value:
        active_entity = {"type": entity_type, "value": entity_value}

    if pivot_to_timeline and entity_value:
        queue_timeline_pivot(entity_type, entity_value)

    if not active_entity or not active_entity.get("value"):
        st.info("Enter an entity value and click Open Entity.")
        return

    entity_type = active_entity["type"]
    entity_value = active_entity["value"]
    st.markdown(f"**Entity:** `{entity_type}` = `{entity_value}`")

    entity_clause, entity_params = entity_where_clause(entity_type, entity_value)
    base_where = f"e.case_id = ? AND {entity_clause}"
    base_params: List[str] = [case_id] + entity_params

    tabs = st.tabs(["Overview", "Relationships", "Events", "Notes / Tags", "Coverage"])

    with tabs[0]:
        summary = query_one(
            case_id,
            f"""
            SELECT MIN(e.event_ts) AS first_seen,
                   MAX(e.event_ts) AS last_seen,
                   COUNT(*) AS total_events
            FROM events e
            WHERE {base_where}
            """,
            tuple(base_params),
        )
        if not summary or summary["total_events"] == 0:
            st.warning("No events found for this entity.")
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("First Seen", summary["first_seen"])
        col2.metric("Last Seen", summary["last_seen"])
        col3.metric("Total Events", summary["total_events"])

        if table_exists(case_id, "entity_aliases"):
            aliases_df = query_df(
                case_id,
                """
                SELECT alias_value, confidence, source
                FROM entity_aliases
                WHERE case_id = ? AND entity_type = ? AND canonical_value = ?
                ORDER BY confidence DESC
                """,
                (case_id, entity_type, entity_value),
            )
            if not aliases_df.empty:
                st.markdown("#### Aliases")
                st.dataframe(aliases_df, use_container_width=True)

        st.markdown("#### Activity Over Time")
        first_seen = datetime.fromisoformat(summary["first_seen"].replace("Z", "+00:00"))
        last_seen = datetime.fromisoformat(summary["last_seen"].replace("Z", "+00:00"))
        bucket_fmt = "%Y-%m-%d %H:00:00" if (last_seen - first_seen) <= timedelta(hours=48) else "%Y-%m-%d"
        bucket_label = "hour" if bucket_fmt.endswith("%H:00:00") else "day"
        activity_df = query_df(
            case_id,
            f"""
            SELECT strftime('{bucket_fmt}', e.event_ts) AS bucket, COUNT(*) AS count
            FROM events e
            WHERE {base_where}
            GROUP BY bucket
            ORDER BY bucket
            """,
            tuple(base_params),
        )
        if not activity_df.empty:
            chart = alt.Chart(activity_df).mark_line(point=True).encode(
                x=alt.X("bucket:T", title=f"Time ({bucket_label})"),
                y=alt.Y("count:Q", title="Events"),
                tooltip=["bucket:T", "count:Q"],
            )
            st.altair_chart(chart, use_container_width=True)

        st.markdown("#### Event Count by Source")
        source_df = query_df(
            case_id,
            f"""
            SELECT e.source_system, COUNT(*) AS count
            FROM events e
            WHERE {base_where}
            GROUP BY e.source_system
            ORDER BY count DESC
            """,
            tuple(base_params),
        )
        st.dataframe(source_df, use_container_width=True)

        st.markdown("#### Event Count by Type")
        type_df = query_df(
            case_id,
            f"""
            SELECT e.event_type, COUNT(*) AS count
            FROM events e
            WHERE {base_where}
            GROUP BY e.event_type
            ORDER BY count DESC
            """,
            tuple(base_params),
        )
        st.dataframe(type_df, use_container_width=True)

    with tabs[1]:
        related_groups = RELATED_ENTITY_MAP.get(entity_type, [])
        for title, field, target_type in related_groups:
            render_related_entities(
                case_id,
                title,
                field,
                target_type,
                base_where,
                base_params,
            )

    with tabs[2]:
        st.markdown("#### Recent Events")
        recent_df = query_df(
            case_id,
            f"""
            SELECT
              e.event_pk, e.event_ts, e.source_system, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
              e.process_name, e.outcome, e.severity, e.message, e.raw_json, e.raw_ref, e.run_id
            FROM events e
            WHERE {base_where}
            ORDER BY e.event_ts DESC
            LIMIT 200
            """,
            tuple(base_params),
        )
        if recent_df.empty:
            st.info("No events available for this entity.")
        else:
            st.dataframe(
                recent_df[
                    [
                        "event_ts",
                        "source_system",
                        "event_type",
                        "host",
                        "user",
                        "src_ip",
                        "dest_ip",
                        "process_name",
                        "outcome",
                        "severity",
                        "message",
                    ]
                ],
                use_container_width=True,
            )
            selected_pk = st.selectbox("Select an event to inspect", recent_df["event_pk"].tolist())
            selected = recent_df[recent_df["event_pk"] == selected_pk].iloc[0].to_dict()
            st.markdown("#### Event Provenance")
            st.write({"run_id": selected["run_id"], "source_system": selected["source_system"]})
            if selected.get("raw_json"):
                st.markdown("#### Raw JSON")
                st.json(selected["raw_json"])
            else:
                st.write({"raw_ref": selected.get("raw_ref")})

        st.markdown("#### Top Interesting Events")
        interesting_df = query_df(
            case_id,
            f"""
            SELECT
              e.event_ts, e.source_system, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
              e.process_name, e.outcome, e.severity, e.message, e.run_id
            FROM events e
            WHERE {base_where}
            ORDER BY e.event_ts DESC
            LIMIT 1000
            """,
            tuple(base_params),
        )
        if interesting_df.empty:
            st.caption("No events to score.")
        else:
            event_type_counts = load_case_event_type_counts(case_id)
            window_start = datetime.fromisoformat(summary["first_seen"].replace("Z", "+00:00"))
            window_end = datetime.fromisoformat(summary["last_seen"].replace("Z", "+00:00"))
            scored = []
            for _, row in interesting_df.iterrows():
                event = row.to_dict()
                score = score_event(event, event_type_counts, window_end, window_start)
                event["score"] = score
                scored.append(event)
            scored_sorted = sorted(scored, key=lambda item: item["score"], reverse=True)[:50]
            scored_df = pd.DataFrame(scored_sorted)
            if not scored_df.empty:
                st.dataframe(
                    scored_df[
                        [
                            "score",
                            "event_ts",
                            "source_system",
                            "event_type",
                            "host",
                            "user",
                            "src_ip",
                            "dest_ip",
                            "process_name",
                            "outcome",
                            "severity",
                            "message",
                            "run_id",
                        ]
                    ],
                    use_container_width=True,
                )

    with tabs[3]:
        if table_exists(case_id, "entity_notes"):
            notes_row = query_one(
                case_id,
                """
                SELECT notes, tags
                FROM entity_notes
                WHERE case_id = ? AND entity_type = ? AND entity_value = ?
                """,
                (case_id, entity_type, entity_value),
            )
            notes_value = notes_row["notes"] if notes_row else ""
            tags_value = notes_row["tags"] if notes_row else ""
            notes = st.text_area("Notes", value=notes_value, height=150)
            tags = st.text_input("Tags (comma-separated)", value=tags_value)
            if st.button("Save Notes"):
                with sqlite3.connect(db_path(case_id)) as conn:
                    conn.execute(
                        """
                        DELETE FROM entity_notes
                        WHERE case_id = ? AND entity_type = ? AND entity_value = ?
                        """,
                        (case_id, entity_type, entity_value),
                    )
                    conn.execute(
                        """
                        INSERT INTO entity_notes(case_id, entity_type, entity_value, notes, tags)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (case_id, entity_type, entity_value, notes, tags),
                    )
                st.success("Notes saved.")
        else:
            key_notes = f"notes:{case_id}:{entity_type}:{entity_value}"
            key_tags = f"tags:{case_id}:{entity_type}:{entity_value}"
            notes = st.text_area("Notes", value=st.session_state.get(key_notes, ""), height=150)
            tags = st.text_input("Tags (comma-separated)", value=st.session_state.get(key_tags, ""))
            if st.button("Save Notes (Session Only)"):
                st.session_state[key_notes] = notes
                st.session_state[key_tags] = tags
                st.success("Notes stored in session.")

    with tabs[4]:
        if not table_exists(case_id, "query_runs"):
            st.info("No query run metadata available.")
        else:
            coverage_df = query_df(
                case_id,
                f"""
                SELECT q.run_id, q.source_system, q.query_name, q.executed_at, q.time_start, q.time_end,
                       COUNT(*) AS event_count
                FROM events e
                JOIN query_runs q ON e.run_id = q.run_id
                WHERE {base_where}
                GROUP BY q.run_id, q.source_system, q.query_name, q.executed_at, q.time_start, q.time_end
                ORDER BY q.executed_at DESC
                """,
                tuple(base_params),
            )
            st.dataframe(coverage_df, use_container_width=True)
            source_cov = query_df(
                case_id,
                f"""
                SELECT q.source_system, COUNT(*) AS event_count
                FROM events e
                JOIN query_runs q ON e.run_id = q.run_id
                WHERE {base_where}
                GROUP BY q.source_system
                ORDER BY event_count DESC
                """,
                tuple(base_params),
            )
            st.markdown("#### Coverage by Source")
            st.dataframe(source_cov, use_container_width=True)


def page_ask_ai(case_id: str) -> None:
    st.subheader("Ask AI (Stub)")
    question = st.text_input("Question")
    if not question:
        st.info("Ask a question to see the suggested SQL.")
        return

    st.markdown("### Suggested SQL")
    suggested_sql = """
SELECT event_type, COUNT(*) AS count
FROM events
WHERE case_id = ?
GROUP BY event_type
ORDER BY count DESC
"""
    st.code(suggested_sql.strip(), language="sql")
    st.markdown("### Suggested Visualization")
    st.write("bar chart")
    st.caption("This is a placeholder. Wire in your LLM provider to generate SQL safely.")


def main() -> None:
    st.title("Investigation Workbench")

    cases = list_cases()
    if not cases:
        st.warning("No cases found. Run `python -m cli init-case <case_id>` first.")
        return

    case_id = st.sidebar.selectbox("Case", cases)
    next_page = st.session_state.pop("next_page", None)
    if next_page:
        st.session_state["selected_page"] = next_page
    pages = {
        "Case Overview": page_case_overview,
        "Timeline Explorer": page_timeline,
        "Swimlane Timeline": page_swimlane_timeline,
        "Entity Page": page_entity_page,
        "Ask AI (Stub)": page_ask_ai,
    }
    if FEATURE_ENTITY_EXPLORER:
        pages["Entity Explorer"] = page_entity_explorer
    page = st.sidebar.radio("Page", list(pages.keys()), key="selected_page")
    pages[page](case_id)


if __name__ == "__main__":
    main()
