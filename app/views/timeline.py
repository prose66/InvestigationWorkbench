from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from services.bookmarks import get_bookmarked_pks, toggle_bookmark
from services.db import distinct_values, query_df, time_bounds
from services.entities import load_case_event_type_counts
from services.filters import (
    build_filters,
    get_preset_names,
    get_preset_by_name,
    apply_preset_to_query,
)
from services.gaps import detect_timeline_gaps, get_source_coverage
from services.markers import add_timeline_marker, delete_timeline_marker, get_timeline_markers
from services.scoring import score_event
from state import (
    get_filter_state,
    save_filter_state,
    clear_filter_state,
    queue_entity_navigation,
    queue_timeline_pivot,
    get_pivot_entities,
    remove_pivot_entity,
    clear_pivot_entities,
)


def timeline_bucket_format(start_dt: datetime, end_dt: datetime) -> tuple[str, str]:
    delta = end_dt - start_dt
    if delta > timedelta(days=30):
        return "%Y-%m-%d", "day"
    if delta > timedelta(days=2):
        return "%Y-%m-%d %H:00:00", "hour"
    return "%Y-%m-%d %H:%M:00", "minute"


def _severity_class(severity: str) -> str:
    """Map severity to CSS class name."""
    severity_lower = (severity or "").lower()
    if severity_lower in ("high", "critical"):
        return "severity-high"
    if severity_lower == "medium":
        return "severity-medium"
    return "severity-low"


def page_timeline(case_id: str) -> None:
    st.subheader("Timeline Explorer")
    min_ts, max_ts = time_bounds(case_id)
    if not min_ts or not max_ts:
        st.info("No events ingested yet.")
        return

    # Handle multi-entity pivot chain
    pivot_entities = get_pivot_entities()
    if pivot_entities:
        st.markdown("#### Active Pivot Filters")
        pivot_cols = st.columns(min(len(pivot_entities) + 1, 6))
        for idx, pivot in enumerate(pivot_entities):
            with pivot_cols[idx % 5]:
                col_label = pivot.get("type", pivot["column"])
                if st.button(
                    f"{col_label}={pivot['value'][:15]} X",
                    key=f"remove_pivot_{idx}",
                    help=f"Remove filter: {pivot['column']}={pivot['value']}",
                ):
                    remove_pivot_entity(idx)
                    st.rerun()
        with pivot_cols[min(len(pivot_entities), 5)]:
            if st.button("Clear All", key="clear_all_pivots"):
                clear_pivot_entities()
                st.rerun()
        # Display filter chain description
        pivot_chain = " AND ".join(
            [f"{p.get('type', p['column'])}={p['value']}" for p in pivot_entities]
        )
        st.info(f"Filtering: {pivot_chain}")

    # Handle filter from overview drill-down
    timeline_filter = st.session_state.pop("timeline_filter", None)

    # Load distinct values for filter options
    sources = distinct_values(case_id, "source_system")
    event_types = distinct_values(case_id, "event_type")
    hosts = distinct_values(case_id, "host")
    users = distinct_values(case_id, "user")
    ips = sorted(set(distinct_values(case_id, "src_ip") + distinct_values(case_id, "dest_ip")))
    processes = distinct_values(case_id, "process_name")
    hashes = distinct_values(case_id, "file_hash")

    # Load persisted filter state
    saved_filters = get_filter_state(case_id, "timeline")

    # --- SIDEBAR: All Controls ---
    with st.sidebar:
        st.markdown("### Timeline Controls")

        # Time range
        st.markdown("#### Time Range")
        start_date, end_date = st.date_input(
            "Date range",
            value=(
                saved_filters.get("start_date", min_ts.date()),
                saved_filters.get("end_date", max_ts.date()),
            ),
            min_value=min_ts.date(),
            max_value=max_ts.date(),
            key="timeline_date_range",
        )
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        # Quick filter presets
        st.markdown("#### Quick Filters")
        preset_name = st.selectbox(
            "Filter preset",
            get_preset_names(),
            index=0,
            key="filter_preset",
        )
        selected_preset = get_preset_by_name(preset_name) if preset_name != "Custom..." else None

        # Detailed filters in expander (collapsed by default unless Custom selected)
        with st.expander("Detailed Filters", expanded=(preset_name == "Custom...")):
            # Apply defaults from multi-entity pivots or timeline_filter
            default_hosts = saved_filters.get("hosts", [])
            default_users = saved_filters.get("users", [])
            default_ips = saved_filters.get("ips", [])
            default_processes = saved_filters.get("processes", [])
            default_hashes = saved_filters.get("hashes", [])

            # Apply pivot entities to defaults
            for pivot in pivot_entities:
                if pivot["column"] == "host" and pivot["value"] not in default_hosts:
                    default_hosts = default_hosts + [pivot["value"]]
                elif pivot["column"] == "user" and pivot["value"] not in default_users:
                    default_users = default_users + [pivot["value"]]
                elif pivot["column"] == "src_ip" and pivot["value"] not in default_ips:
                    default_ips = default_ips + [pivot["value"]]
                elif pivot["column"] == "process_name" and pivot["value"] not in default_processes:
                    default_processes = default_processes + [pivot["value"]]
                elif pivot["column"] == "file_hash" and pivot["value"] not in default_hashes:
                    default_hashes = default_hashes + [pivot["value"]]

            default_sources = [timeline_filter["value"]] if timeline_filter and timeline_filter["type"] == "source_system" else saved_filters.get("sources", [])
            default_event_types = [timeline_filter["value"]] if timeline_filter and timeline_filter["type"] == "event_type" else saved_filters.get("event_types", [])

            # 2-column layout for filters
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                selected_sources = st.multiselect("Source", sources, default=default_sources, key="f_sources")
                selected_hosts = st.multiselect("Host", hosts, default=default_hosts, key="f_hosts")
                selected_ips = st.multiselect("IP", ips, default=default_ips, key="f_ips")
                selected_hashes = st.multiselect("Hash", hashes, default=default_hashes, key="f_hashes")

            with fcol2:
                selected_event_types = st.multiselect("Event Type", event_types, default=default_event_types, key="f_event_types")
                selected_users = st.multiselect("User", users, default=default_users, key="f_users")
                selected_processes = st.multiselect("Process", processes, default=default_processes, key="f_processes")

            if st.button("Clear Filters", key="clear_filters"):
                clear_filter_state(case_id, "timeline")
                st.rerun()

        # Save current filter state
        current_filters = {
            "start_date": start_date,
            "end_date": end_date,
            "sources": selected_sources if preset_name == "Custom..." else [],
            "event_types": selected_event_types if preset_name == "Custom..." else [],
            "hosts": selected_hosts if preset_name == "Custom..." else [],
            "users": selected_users if preset_name == "Custom..." else [],
            "ips": selected_ips if preset_name == "Custom..." else [],
            "processes": selected_processes if preset_name == "Custom..." else [],
            "hashes": selected_hashes if preset_name == "Custom..." else [],
        }
        save_filter_state(case_id, "timeline", current_filters)

        # Display settings
        st.markdown("#### Display")
        page_size = st.selectbox("Rows per page", [25, 50, 100], index=1, key="page_size")
        sort_by = st.selectbox(
            "Sort by",
            ["Time (oldest first)", "Time (newest first)", "Score (highest first)"],
            index=0,
            key="sort_by",
        )

        # Timeline Markers (moved from main area)
        st.markdown("---")
        st.markdown("#### Timeline Markers")
        with st.expander("Add Marker"):
            new_marker_ts = st.text_input("Timestamp (ISO8601)", key="marker_ts")
            new_marker_label = st.text_input("Label", key="marker_label")
            new_marker_desc = st.text_input("Description", key="marker_desc")
            marker_color = st.color_picker("Color", value="#ff6b6b", key="marker_color")
            if st.button("Add Marker", key="add_marker") and new_marker_ts and new_marker_label:
                try:
                    add_timeline_marker(case_id, new_marker_ts, new_marker_label, new_marker_desc, marker_color)
                    st.success(f"Added: {new_marker_label}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed: {exc}")

        existing_markers = get_timeline_markers(case_id)
        if not existing_markers.empty:
            for _, marker in existing_markers.iterrows():
                mcol1, mcol2 = st.columns([3, 1])
                mcol1.caption(f"{marker['label']} - {marker['marker_ts'][:16]}")
                if mcol2.button("X", key=f"del_marker_{marker['marker_id']}"):
                    delete_timeline_marker(case_id, int(marker["marker_id"]))
                    st.rerun()

    # Build query filters
    if preset_name == "Custom...":
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
    else:
        # Start with base filters (no custom selections)
        where_clause, params = build_filters(
            case_id,
            start_dt,
            end_dt,
            [], [], [], [], [], [], [],
        )
        # Apply preset
        if selected_preset:
            where_clause, params = apply_preset_to_query(selected_preset, where_clause, params)

    # --- GAP DETECTION (Promoted - visible without scrolling) ---
    gap_bucket_mins = 60
    min_gap_buckets = 2
    _, gaps = detect_timeline_gaps(
        case_id,
        bucket_minutes=gap_bucket_mins,
        min_gap_buckets=min_gap_buckets,
    )

    if gaps:
        # Sort by severity and show top 3 inline
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_gaps = sorted(gaps, key=lambda g: severity_order.get(g.severity, 3))
        top_gaps = sorted_gaps[:3]

        for gap in top_gaps:
            dur_str = str(gap.duration).split(".")[0]
            sources_str = ", ".join(gap.affected_sources[:3]) if gap.affected_sources else "Unknown"

            if gap.severity == "high":
                st.error(
                    f"**Coverage Gap:** {gap.start.strftime('%m/%d %H:%M')} - {gap.end.strftime('%m/%d %H:%M')} "
                    f"({dur_str}) | Sources: {sources_str}"
                )
            elif gap.severity == "medium":
                st.warning(
                    f"**Coverage Gap:** {gap.start.strftime('%m/%d %H:%M')} - {gap.end.strftime('%m/%d %H:%M')} "
                    f"({dur_str}) | Sources: {sources_str}"
                )
            else:
                st.info(
                    f"**Coverage Gap:** {gap.start.strftime('%m/%d %H:%M')} - {gap.end.strftime('%m/%d %H:%M')} "
                    f"({dur_str})"
                )

        if len(gaps) > 3:
            with st.expander(f"View all {len(gaps)} gaps"):
                for gap in sorted_gaps[3:]:
                    dur_str = str(gap.duration).split(".")[0]
                    st.caption(
                        f"{gap.severity.upper()}: {gap.start.strftime('%m/%d %H:%M')} - "
                        f"{gap.end.strftime('%m/%d %H:%M')} ({dur_str})"
                    )

    # --- INTERACTIVE CHART ---
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

    # Track chart selection in session state
    chart_selection = st.session_state.get("chart_bucket_selection")

    if not timeline_df.empty:
        timeline_df["bucket_dt"] = pd.to_datetime(timeline_df["bucket"], utc=True)

        # Create selection parameter for drill-down
        brush = alt.selection_point(fields=["bucket"], name="bucket_select")

        base_chart = alt.Chart(timeline_df).mark_bar().encode(
            x=alt.X("bucket_dt:T", title=f"Time ({bucket_label})"),
            y=alt.Y("count:Q", title="Events"),
            tooltip=["bucket:N", "count:Q"],
            opacity=alt.condition(brush, alt.value(1), alt.value(0.5)),
            color=alt.condition(brush, alt.value("#1f77b4"), alt.value("#aec7e8")),
        ).add_params(brush)

        # Add markers overlay
        markers_df = get_timeline_markers(case_id)
        if not markers_df.empty:
            markers_df["marker_ts"] = pd.to_datetime(markers_df["marker_ts"], utc=True)
            marker_rules = alt.Chart(markers_df).mark_rule(
                strokeDash=[4, 4],
                strokeWidth=2,
            ).encode(
                x="marker_ts:T",
                color=alt.Color("color:N", scale=None),
                tooltip=["label:N", "marker_ts:T", "description:N"],
            )
            marker_labels = alt.Chart(markers_df).mark_text(
                align="left",
                dx=4,
                dy=-6,
                fontSize=10,
            ).encode(
                x="marker_ts:T",
                text="label:N",
                color=alt.value("gray"),
            )
            chart = base_chart + marker_rules + marker_labels
        else:
            chart = base_chart

        chart_state = st.altair_chart(
            chart,
            use_container_width=True,
            on_select="rerun",
            selection_mode="bucket_select",
        )

        # Handle chart selection
        selection_data = getattr(chart_state, "selection", None) or {}
        bucket_select = selection_data.get("bucket_select")
        if isinstance(bucket_select, dict) and bucket_select.get("bucket"):
            selected_buckets = bucket_select["bucket"]
            if selected_buckets:
                st.session_state["chart_bucket_selection"] = selected_buckets[0] if isinstance(selected_buckets, list) else selected_buckets
        elif isinstance(bucket_select, list) and bucket_select:
            first_sel = bucket_select[0]
            if isinstance(first_sel, dict) and first_sel.get("bucket"):
                st.session_state["chart_bucket_selection"] = first_sel["bucket"]

        chart_selection = st.session_state.get("chart_bucket_selection")
        if chart_selection:
            ccol1, ccol2 = st.columns([4, 1])
            ccol1.info(f"Filtering to bucket: {chart_selection}")
            if ccol2.button("Clear Selection", key="clear_chart_sel"):
                st.session_state.pop("chart_bucket_selection", None)
                st.rerun()
    else:
        st.warning("No events match the selected filters.")
        chart_selection = None

    # --- PAGINATION with Prev/Next buttons ---
    # Get total count for pagination
    count_sql = f"""
        SELECT COUNT(*) as cnt FROM events e WHERE {where_clause}
    """
    if chart_selection:
        count_sql = f"""
            SELECT COUNT(*) as cnt FROM events e
            WHERE {where_clause} AND strftime('{bucket_fmt}', e.event_ts) = ?
        """
        count_params = tuple(params + [chart_selection])
    else:
        count_params = tuple(params)

    count_result = query_df(case_id, count_sql, count_params)
    total_events = int(count_result.iloc[0]["cnt"]) if not count_result.empty else 0
    total_pages = max(1, (total_events + page_size - 1) // page_size)

    # Page state
    if "timeline_page" not in st.session_state:
        st.session_state["timeline_page"] = 1
    current_page = st.session_state["timeline_page"]
    current_page = max(1, min(current_page, total_pages))

    # Pagination controls
    pcol1, pcol2, pcol3, pcol4, pcol5, pcol6 = st.columns([1, 1, 1, 1, 2, 2])
    with pcol1:
        if st.button("First", disabled=(current_page == 1), key="pg_first"):
            st.session_state["timeline_page"] = 1
            st.rerun()
    with pcol2:
        if st.button("Prev", disabled=(current_page == 1), key="pg_prev"):
            st.session_state["timeline_page"] = current_page - 1
            st.rerun()
    with pcol3:
        if st.button("Next", disabled=(current_page >= total_pages), key="pg_next"):
            st.session_state["timeline_page"] = current_page + 1
            st.rerun()
    with pcol4:
        if st.button("Last", disabled=(current_page >= total_pages), key="pg_last"):
            st.session_state["timeline_page"] = total_pages
            st.rerun()
    with pcol5:
        st.caption(f"Page {current_page} of {total_pages}")
    with pcol6:
        st.caption(f"({total_events:,} events)")

    offset = (current_page - 1) * page_size

    # Build sort clause
    sort_clause = "e.event_ts ASC"
    if sort_by == "Time (newest first)":
        sort_clause = "e.event_ts DESC"
    # Score sorting handled after query

    # Build events query
    chart_filter = ""
    events_params = list(params)
    if chart_selection:
        chart_filter = f" AND strftime('{bucket_fmt}', e.event_ts) = ?"
        events_params.append(chart_selection)

    events_df = query_df(
        case_id,
        f"""
        SELECT
          e.event_pk, e.event_ts, e.source_system, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
          e.process_name, e.process_cmdline, e.process_id, e.parent_pid, e.parent_process_name, e.parent_process_cmdline,
          e.registry_hive, e.registry_key, e.registry_value_name, e.registry_value_type, e.registry_value_data,
          e.tactic, e.technique, e.outcome, e.severity, e.message,
          e.source_event_id, e.raw_ref, e.raw_json,
          q.run_id, q.query_name, q.executed_at, q.time_start, q.time_end
        FROM events e
        JOIN query_runs q ON e.run_id = q.run_id
        WHERE {where_clause}{chart_filter}
        ORDER BY {sort_clause}
        LIMIT ? OFFSET ?
        """,
        tuple(events_params + [page_size, offset]),
    )

    # Calculate scores if needed
    if not events_df.empty:
        event_type_counts = load_case_event_type_counts(case_id, query_df)
        window_start = min_ts
        window_end = max_ts

        scores = []
        for _, row in events_df.iterrows():
            event = row.to_dict()
            score = score_event(event, event_type_counts, window_end, window_start)
            scores.append(score)
        events_df["score"] = scores

        if sort_by == "Score (highest first)":
            events_df = events_df.sort_values("score", ascending=False)

    # Bookmarks
    bookmarked_pks = get_bookmarked_pks(case_id)
    if not events_df.empty:
        events_df["bookmarked"] = events_df["event_pk"].apply(lambda pk: "*" if pk in bookmarked_pks else "")

    # Display columns (including MITRE and score)
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
        "tactic",
        "technique",
        "score",
        "message",
    ]
    # Filter to columns that exist
    display_cols = [c for c in display_cols if c in events_df.columns]

    if not events_df.empty:
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

        if selected_pk is None and not events_df.empty:
            selected_pk = st.selectbox(
                "Select an event for details",
                events_df["event_pk"].tolist(),
                key="event_select",
            )

        if selected_pk is not None:
            selected = events_df[events_df["event_pk"] == selected_pk].iloc[0].to_dict()

            # --- ONE-CLICK PIVOT BUTTONS ---
            st.markdown("#### Quick Pivot")
            pivot_entities = []
            if selected.get("host"):
                pivot_entities.append(("host", selected["host"]))
            if selected.get("user"):
                pivot_entities.append(("user", selected["user"]))
            if selected.get("src_ip"):
                pivot_entities.append(("ip", selected["src_ip"]))
            if selected.get("dest_ip") and selected["dest_ip"] != selected.get("src_ip"):
                pivot_entities.append(("ip", selected["dest_ip"]))
            if selected.get("process_name"):
                pivot_entities.append(("process", selected["process_name"]))

            if pivot_entities:
                cols = st.columns(min(len(pivot_entities) * 2, 6))
                col_idx = 0
                for entity_type, entity_value in pivot_entities[:3]:
                    with cols[col_idx]:
                        if st.button(f"Timeline: {entity_value[:15]}", key=f"pivot_tl_{entity_type}_{entity_value}"):
                            queue_timeline_pivot(entity_type, entity_value)
                            st.rerun()
                    col_idx += 1
                    if col_idx < len(cols):
                        with cols[col_idx]:
                            if st.button(f"Entity: {entity_value[:15]}", key=f"pivot_ent_{entity_type}_{entity_value}"):
                                queue_entity_navigation(entity_type, entity_value)
                                st.rerun()
                        col_idx += 1

            # Bookmark button
            is_currently_bookmarked = selected_pk in bookmarked_pks
            bookmark_label = "Remove Bookmark" if is_currently_bookmarked else "Bookmark Event"
            if st.button(bookmark_label, key="toggle_bookmark"):
                toggle_bookmark(case_id, selected_pk)
                st.rerun()

            # --- PROCESS CHAIN (if available) ---
            if selected.get("parent_process_name") or selected.get("process_name"):
                st.markdown("#### Process Chain")
                chain_cols = st.columns(2)
                with chain_cols[0]:
                    if selected.get("parent_process_name"):
                        st.markdown("**Parent Process**")
                        st.code(f"PID: {selected.get('parent_pid', 'N/A')}\n{selected.get('parent_process_name', 'N/A')}")
                        if selected.get("parent_process_cmdline"):
                            st.caption(f"Cmdline: {selected['parent_process_cmdline'][:100]}")
                with chain_cols[1]:
                    if selected.get("process_name"):
                        st.markdown("**Current Process**")
                        st.code(f"PID: {selected.get('process_id', 'N/A')}\n{selected.get('process_name', 'N/A')}")
                        if selected.get("process_cmdline"):
                            st.caption(f"Cmdline: {selected['process_cmdline'][:100]}")

            # --- REGISTRY DETAILS (if available) ---
            if selected.get("registry_key") or selected.get("registry_hive"):
                st.markdown("#### Registry Details")
                reg_data = {
                    "Hive": selected.get("registry_hive", ""),
                    "Key": selected.get("registry_key", ""),
                    "Value Name": selected.get("registry_value_name", ""),
                    "Value Type": selected.get("registry_value_type", ""),
                    "Value Data": selected.get("registry_value_data", ""),
                }
                # Filter out empty values
                reg_data = {k: v for k, v in reg_data.items() if v}
                if reg_data:
                    for key, value in reg_data.items():
                        st.text(f"{key}: {value}")

            # --- EVENT PROVENANCE ---
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

    # --- EXPORT (moved to bottom, simplified) ---
    with st.expander("Export & Coverage"):
        export_cols = st.columns([2, 1, 1])
        with export_cols[0]:
            export_limit = st.selectbox("Export limit", [100, 500, 1000, 5000, "All"], index=1, key="export_limit")

        export_sql_limit = "" if export_limit == "All" else f"LIMIT {export_limit}"
        export_df = query_df(
            case_id,
            f"""
            SELECT
              e.event_ts, e.source_system, e.event_type, e.host, e.user, e.src_ip, e.dest_ip,
              e.process_name, e.tactic, e.technique, e.outcome, e.severity, e.message,
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
                "Export CSV",
                data=export_df.to_csv(index=False),
                file_name=f"{case_id}_timeline_export.csv",
                mime="text/csv",
                key="export_csv",
            )
        with export_cols[2]:
            st.caption(f"{len(export_df)} events")

        # Source coverage table
        st.markdown("#### Source Coverage")
        coverage_df = get_source_coverage(case_id)
        if not coverage_df.empty:
            st.dataframe(coverage_df, use_container_width=True, height=200)
