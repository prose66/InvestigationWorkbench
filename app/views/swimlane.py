from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import altair as alt
import pandas as pd
import streamlit as st

from services.db import distinct_values, query_df, time_bounds
from services.filters import build_filters, time_range_selector
from services.entities import RELATED_ENTITY_MAP
from state import queue_entity_navigation


def swimlane_bucket_size(start_dt: datetime, end_dt: datetime) -> tuple[str, timedelta]:
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
