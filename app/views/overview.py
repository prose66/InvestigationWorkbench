from __future__ import annotations

import altair as alt
import streamlit as st

from services.db import query_df, query_one, time_bounds
from services.gaps import get_source_coverage
from state import queue_timeline_filter


def page_case_overview(case_id: str) -> None:
    st.subheader("Case Overview")
    st.caption(f"Case: {case_id}")

    summary = query_one(
        case_id,
        """
        SELECT COUNT(*) AS total_events,
               COUNT(DISTINCT run_id) AS total_runs,
               COUNT(DISTINCT source_system) AS total_sources,
               COUNT(DISTINCT host) AS total_hosts
        FROM events
        WHERE case_id = ?
        """,
        (case_id,),
    )

    # Key metrics in a row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", f"{summary['total_events']:,}" if summary else 0)
    col2.metric("Query Runs", summary["total_runs"] if summary else 0)
    col3.metric("Sources", summary["total_sources"] if summary else 0)
    col4.metric("Unique Hosts", summary["total_hosts"] if summary else 0)

    min_ts, max_ts = time_bounds(case_id)
    if min_ts and max_ts:
        st.info(f"Time coverage: **{min_ts}** to **{max_ts}** (UTC)")
    else:
        st.warning("No events ingested yet. Use the CLI to ingest data.")
        return

    st.markdown("---")

    # --- SOURCE COVERAGE CHART ---
    st.markdown("### Source Coverage")
    coverage_df = get_source_coverage(case_id)
    if not coverage_df.empty:
        # Color-code by coverage percentage
        coverage_df["color"] = coverage_df["coverage_pct"].apply(
            lambda x: "#d32f2f" if x < 25 else "#f57c00" if x < 50 else "#388e3c"
        )

        coverage_chart = alt.Chart(coverage_df).mark_bar().encode(
            x=alt.X("coverage_pct:Q", title="Coverage %", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("source_system:N", title="Source", sort="-x"),
            color=alt.Color("color:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("source_system:N", title="Source"),
                alt.Tooltip("coverage_pct:Q", title="Coverage %", format=".1f"),
                alt.Tooltip("event_count:Q", title="Events", format=","),
                alt.Tooltip("active_hours:Q", title="Active Hours"),
            ],
        ).properties(height=max(150, len(coverage_df) * 30))

        st.altair_chart(coverage_chart, use_container_width=True)

        # Coverage legend
        lcol1, lcol2, lcol3 = st.columns(3)
        lcol1.caption("Red: <25%")
        lcol2.caption("Orange: 25-50%")
        lcol3.caption("Green: >50%")

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
                    f"{row['source_system']}\n({row['count']:,} events)",
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
                    f"{row['event_type']}\n({row['count']:,})",
                    key=f"type_{row['event_type']}",
                    use_container_width=True,
                ):
                    queue_timeline_filter("event_type", row["event_type"])
                    st.rerun()

        # Full table
        st.dataframe(type_df, use_container_width=True)

    # --- MITRE ATT&CK COVERAGE ---
    st.markdown("### MITRE ATT&CK Coverage")
    mitre_df = query_df(
        case_id,
        """
        SELECT tactic, technique, COUNT(*) AS count
        FROM events
        WHERE case_id = ?
          AND tactic IS NOT NULL
          AND tactic != ''
        GROUP BY tactic, technique
        ORDER BY tactic, count DESC
        """,
        (case_id,),
    )

    if mitre_df.empty:
        st.caption("No MITRE ATT&CK data available. Events need tactic/technique fields populated.")
    else:
        # Group by tactic for the main chart
        tactic_df = mitre_df.groupby("tactic", as_index=False).agg(
            count=("count", "sum"),
            techniques=("technique", lambda x: len(x.dropna().unique())),
        ).sort_values("count", ascending=False)

        # Tactic coverage chart
        tactic_chart = alt.Chart(tactic_df).mark_bar().encode(
            x=alt.X("count:Q", title="Events"),
            y=alt.Y("tactic:N", title="Tactic", sort="-x"),
            color=alt.Color("tactic:N", legend=None),
            tooltip=[
                alt.Tooltip("tactic:N", title="Tactic"),
                alt.Tooltip("count:Q", title="Events", format=","),
                alt.Tooltip("techniques:Q", title="Techniques"),
            ],
        ).properties(height=max(150, len(tactic_df) * 35))

        st.altair_chart(tactic_chart, use_container_width=True)

        # Technique breakdown in expander
        with st.expander("Technique Breakdown"):
            for tactic in tactic_df["tactic"].tolist():
                st.markdown(f"**{tactic}**")
                tech_subset = mitre_df[mitre_df["tactic"] == tactic][["technique", "count"]]
                tech_subset = tech_subset[tech_subset["technique"].notna()]
                if not tech_subset.empty:
                    st.dataframe(tech_subset, use_container_width=True, hide_index=True)
                else:
                    st.caption("No techniques specified")

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
