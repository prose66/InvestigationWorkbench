from __future__ import annotations

import altair as alt
import streamlit as st

from services.db import query_df, query_one, time_bounds
from state import queue_timeline_filter


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

    st.markdown("### Counts by Source System")
    st.caption("Click a source to view in Timeline Explorer")
    source_df = query_df(
        case_id,
        "SELECT source_system, COUNT(*) AS count FROM events WHERE case_id = ? GROUP BY source_system",
        (case_id,),
    )
    if not source_df.empty:
        # Create clickable buttons for each source
        cols = st.columns(min(len(source_df), 4))
        for i, (_, row) in enumerate(source_df.iterrows()):
            with cols[i % 4]:
                if st.button(
                    f"📊 {row['source_system']}\n({row['count']:,} events)",
                    key=f"source_{row['source_system']}",
                    use_container_width=True,
                ):
                    queue_timeline_filter("source_system", row["source_system"])
                    st.rerun()
        
        # Also show the chart
        chart = alt.Chart(source_df).mark_bar().encode(
            x=alt.X("source_system:N", title="Source System"),
            y=alt.Y("count:Q", title="Events"),
            tooltip=["source_system:N", "count:Q"],
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("### Counts by Event Type")
    st.caption("Click an event type to view in Timeline Explorer")
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
    
    if not type_df.empty:
        # Show top event types as clickable buttons
        top_types = type_df.head(8)
        cols = st.columns(min(len(top_types), 4))
        for i, (_, row) in enumerate(top_types.iterrows()):
            with cols[i % 4]:
                if st.button(
                    f"🏷️ {row['event_type']}\n({row['count']:,})",
                    key=f"type_{row['event_type']}",
                    use_container_width=True,
                ):
                    queue_timeline_filter("event_type", row["event_type"])
                    st.rerun()
        
        # Full table
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
