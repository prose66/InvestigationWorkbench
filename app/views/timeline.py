from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, timezone

from services.bookmarks import get_bookmarked_pks, toggle_bookmark
from services.db import distinct_values, query_df, time_bounds
from services.filters import build_filters
from services.gaps import detect_timeline_gaps, get_source_coverage
from services.markers import add_timeline_marker, delete_timeline_marker, get_timeline_markers


def timeline_bucket_format(start_dt: datetime, end_dt: datetime) -> tuple[str, str]:
    delta = end_dt - start_dt
    if delta > timedelta(days=30):
        return "%Y-%m-%d", "day"
    if delta > timedelta(days=2):
        return "%Y-%m-%d %H:00:00", "hour"
    return "%Y-%m-%d %H:%M:00", "minute"


def page_timeline(case_id: str) -> None:
    st.subheader("Timeline Explorer")
    min_ts, max_ts = time_bounds(case_id)
    if not min_ts or not max_ts:
        st.info("No events ingested yet.")
        return

    # Handle pivot from entity page
    pivot = st.session_state.get("timeline_pivot")
    if pivot:
        st.info(f"Pivot active: {pivot['column']} = {pivot['value']}")
        if st.button("Clear pivot", key="clear_pivot"):
            st.session_state.pop("timeline_pivot", None)
            st.rerun()
    
    # Handle filter from overview drill-down
    timeline_filter = st.session_state.pop("timeline_filter", None)

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
    
    # Apply timeline_filter from overview drill-down
    default_sources = [timeline_filter["value"]] if timeline_filter and timeline_filter["type"] == "source_system" else []
    default_event_types = [timeline_filter["value"]] if timeline_filter and timeline_filter["type"] == "event_type" else []

    col1, col2, col3 = st.columns(3)
    selected_sources = col1.multiselect("Source System", sources, default=default_sources)
    selected_event_types = col2.multiselect("Event Type", event_types, default=default_event_types)
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
        base_chart = alt.Chart(timeline_df).mark_line(point=True).encode(
            x=alt.X("bucket:T", title=f"Time ({bucket_label})"),
            y=alt.Y("count:Q", title="Events"),
            tooltip=["bucket:T", "count:Q"],
        )
        markers_df = get_timeline_markers(case_id)
        if not markers_df.empty:
            markers_df["marker_ts"] = pd.to_datetime(markers_df["marker_ts"], utc=True)
            marker_rules = alt.Chart(markers_df).mark_rule(
                strokeDash=[4, 4],
                strokeWidth=2,
                color=alt.value("#ff6b6b"),
            ).encode(
                x="marker_ts:T",
                tooltip=["label:N", "marker_ts:T", "description:N"],
            )
            marker_labels = alt.Chart(markers_df).mark_text(
                align="left",
                dx=4,
                dy=-6,
                color="gray",
            ).encode(
                x="marker_ts:T",
                text="label:N",
            )
            chart = base_chart + marker_rules + marker_labels
        else:
            chart = base_chart
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No events match the selected filters.")

    # Gap Detection
    with st.expander("⚠️ Coverage Gaps & Data Quality", expanded=False):
        gap_bucket_mins = st.selectbox(
            "Gap detection bucket size",
            [30, 60, 120, 360, 1440],
            index=1,
            format_func=lambda x: f"{x} min" if x < 60 else f"{x//60} hour(s)" if x < 1440 else "1 day",
        )
        min_gap_buckets = st.slider("Minimum consecutive empty buckets", 1, 10, 2)
        
        bucket_df, gaps = detect_timeline_gaps(
            case_id,
            bucket_minutes=gap_bucket_mins,
            min_gap_buckets=min_gap_buckets,
        )
        
        if gaps:
            st.warning(f"Found {len(gaps)} coverage gap(s)")
            for gap in gaps:
                severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(gap.severity, "⚪")
                dur_str = str(gap.duration).split(".")[0]  # Remove microseconds
                st.markdown(
                    f"{severity_color} **{gap.start.strftime('%Y-%m-%d %H:%M')} → {gap.end.strftime('%Y-%m-%d %H:%M')}** "
                    f"({dur_str}) | Expected ~{gap.expected_events} events | Sources active before: {', '.join(gap.affected_sources[:5]) or 'N/A'}"
                )
        else:
            st.success("No significant coverage gaps detected.")
        
        # Source coverage table
        st.markdown("#### Source Coverage")
        coverage_df = get_source_coverage(case_id)
        if not coverage_df.empty:
            st.dataframe(coverage_df, use_container_width=True, height=200)

    st.markdown("#### Timeline Markers")
    marker_col1, marker_col2 = st.columns(2)
    new_marker_ts = marker_col1.text_input("Timestamp (ISO8601, e.g. 2024-07-01T12:00:00Z)")
    new_marker_label = marker_col2.text_input("Label")
    new_marker_desc = st.text_input("Description (optional)")
    marker_color = st.color_picker("Color", value="#ff6b6b")
    if st.button("Add Marker") and new_marker_ts and new_marker_label:
        try:
            add_timeline_marker(case_id, new_marker_ts, new_marker_label, new_marker_desc, marker_color)
            st.success(f"Added marker: {new_marker_label}")
        except Exception as exc:
            st.error(f"Failed to add marker: {exc}")

    existing_markers = get_timeline_markers(case_id)
    if not existing_markers.empty:
        for _, marker in existing_markers.iterrows():
            mcol1, mcol2, mcol3 = st.columns([2, 4, 1])
            mcol1.write(f"**{marker['label']}** - {marker['marker_ts']}")
            mcol2.write(marker.get("description") or "")
            if mcol3.button("Delete", key=f"del_marker_{marker['marker_id']}"):
                delete_timeline_marker(case_id, int(marker["marker_id"]))
                st.rerun()

    # Export filtered events
    st.markdown("#### Export")
    export_cols = st.columns([2, 1, 1])
    with export_cols[0]:
        export_limit = st.selectbox("Export limit", [100, 500, 1000, 5000, "All"], index=1)
    
    export_sql_limit = "" if export_limit == "All" else f"LIMIT {export_limit}"
    export_df = query_df(
        case_id,
        f"""
        SELECT
          e.event_ts, e.source_system, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
          e.process_name, e.outcome, e.severity, e.message,
          e.source_event_id, e.raw_ref
        FROM events e
        WHERE {where_clause}
        ORDER BY e.event_ts ASC
        {export_sql_limit}
        """,
        tuple(params),
    )
    with export_cols[1]:
        st.download_button(
            "📥 Export CSV",
            data=export_df.to_csv(index=False),
            file_name=f"{case_id}_timeline_export.csv",
            mime="text/csv",
            key="export_csv",
        )
    with export_cols[2]:
        st.caption(f"{len(export_df)} events")

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

    bookmarked_pks = get_bookmarked_pks(case_id)
    events_df["bookmarked"] = events_df["event_pk"].apply(lambda pk: "⭐" if pk in bookmarked_pks else "")
    display_cols = [
        "bookmarked",
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
    table_state = st.dataframe(
        events_df[display_cols],
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="timeline_events_table",
    )

    selected_pk = None
    selection = getattr(table_state, "selection", None) or {}
    selected_rows = selection.get("rows", []) if isinstance(selection, dict) else []
    if selected_rows:
        selected_pk = int(events_df.iloc[selected_rows[0]]["event_pk"])

    if not events_df.empty and selected_pk is None:
        selected_pk = st.selectbox(
            "Select an event for provenance",
            events_df["event_pk"].tolist(),
        )

    if selected_pk is not None:
        selected = events_df[events_df["event_pk"] == selected_pk].iloc[0].to_dict()
        is_currently_bookmarked = selected_pk in bookmarked_pks
        bookmark_label = "⭐ Remove Bookmark" if is_currently_bookmarked else "☆ Bookmark Event"
        if st.button(bookmark_label, key="toggle_bookmark"):
            toggle_bookmark(case_id, selected_pk)
            st.rerun()
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
