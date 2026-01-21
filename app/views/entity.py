from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import altair as alt
import pandas as pd
import streamlit as st
import sqlite3

from services.db import db_path, query_df, query_one, table_exists
from services.entities import (
    ENTITY_TYPES,
    RELATED_ENTITY_MAP,
    entity_options,
    entity_where_clause,
    load_case_event_type_counts,
)
from services.scoring import score_event
from state import queue_entity_navigation, queue_timeline_pivot


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

        st.markdown("#### Event Count by Source System")
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
            event_type_counts = load_case_event_type_counts(case_id, query_df)
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
            st.markdown("#### Coverage by Source System")
            st.dataframe(source_cov, use_container_width=True)
