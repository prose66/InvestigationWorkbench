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

    add_in_filter(sources, "source")
    add_in_filter(event_types, "event_type")
    add_in_filter(hosts, "host")
    add_in_filter(users, "user")

    if ips:
        placeholders = ", ".join(["?"] * len(ips))
        clauses.append(f"(e.src_ip IN ({placeholders}) OR e.dest_ip IN ({placeholders}))")
        params.extend(ips)
        params.extend(ips)

    return " AND ".join(clauses), params


def timeline_bucket_format(start_dt: datetime, end_dt: datetime) -> Tuple[str, str]:
    delta = end_dt - start_dt
    if delta > timedelta(days=30):
        return "%Y-%m-%d", "day"
    if delta > timedelta(days=2):
        return "%Y-%m-%d %H:00:00", "hour"
    return "%Y-%m-%d %H:%M:00", "minute"


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
        "SELECT source, COUNT(*) AS count FROM events WHERE case_id = ? GROUP BY source",
        (case_id,),
    )
    if not source_df.empty:
        chart = alt.Chart(source_df).mark_bar().encode(
            x=alt.X("source:N", title="Source"),
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
        SELECT run_id, source, query_name, executed_at, time_start, time_end, row_count
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

    sources = distinct_values(case_id, "source")
    event_types = distinct_values(case_id, "event_type")
    hosts = distinct_values(case_id, "host")
    users = distinct_values(case_id, "user")
    ips = sorted(set(distinct_values(case_id, "src_ip") + distinct_values(case_id, "dest_ip")))

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

    col1, col2, col3 = st.columns(3)
    selected_sources = col1.multiselect("Source", sources, default=[])
    selected_event_types = col2.multiselect("Event Type", event_types, default=[])
    selected_hosts = col3.multiselect("Host", hosts, default=default_hosts)

    col4, col5 = st.columns(2)
    selected_users = col4.multiselect("User", users, default=default_users)
    selected_ips = col5.multiselect("IP (src or dest)", ips, default=default_ips)

    where_clause, params = build_filters(
        case_id,
        start_dt,
        end_dt,
        selected_sources,
        selected_event_types,
        selected_hosts,
        selected_users,
        selected_ips,
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
          e.event_pk, e.event_ts, e.source, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
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
                "source",
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
        SELECT event_ts, source, event_type, host, user, src_ip, dest_ip, process_name, outcome, severity, message
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
    pages = {
        "Case Overview": page_case_overview,
        "Timeline Explorer": page_timeline,
        "Entity Explorer": page_entity_explorer,
        "Ask AI (Stub)": page_ask_ai,
    }
    page = st.sidebar.radio("Page", list(pages.keys()))
    pages[page](case_id)


if __name__ == "__main__":
    main()
