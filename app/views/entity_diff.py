"""Entity diff comparison view."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional

import altair as alt
import pandas as pd
import streamlit as st

from services.db import query_df, query_one
from services.entities import ENTITY_TYPES, entity_options, entity_where_clause


def get_entity_summary(case_id: str, entity_type: str, entity_value: str) -> Dict[str, Any]:
    """Get comprehensive summary for an entity."""
    entity_clause, entity_params = entity_where_clause(entity_type, entity_value)
    base_where = f"e.case_id = ? AND {entity_clause}"
    base_params = [case_id] + entity_params
    
    # Basic stats
    stats = query_one(
        case_id,
        f"""
        SELECT 
            COUNT(*) AS total_events,
            COUNT(DISTINCT e.source_system) AS source_count,
            COUNT(DISTINCT e.event_type) AS event_type_count,
            MIN(e.event_ts) AS first_seen,
            MAX(e.event_ts) AS last_seen
        FROM events e
        WHERE {base_where}
        """,
        tuple(base_params),
    )
    
    if not stats or stats["total_events"] == 0:
        return {"exists": False, "entity_type": entity_type, "entity_value": entity_value}
    
    # Event types
    event_types = query_df(
        case_id,
        f"""
        SELECT e.event_type, COUNT(*) AS count
        FROM events e
        WHERE {base_where}
        GROUP BY e.event_type
        ORDER BY count DESC
        LIMIT 20
        """,
        tuple(base_params),
    )
    
    # Source systems
    sources = query_df(
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
    
    # Time distribution (hourly buckets)
    time_dist = query_df(
        case_id,
        f"""
        SELECT strftime('%Y-%m-%d %H:00:00', e.event_ts) AS hour, COUNT(*) AS count
        FROM events e
        WHERE {base_where}
        GROUP BY hour
        ORDER BY hour
        """,
        tuple(base_params),
    )
    
    # Related entities
    related = {}
    related_fields = {
        "host": ["host"],
        "user": ["user"],
        "ip": ["src_ip", "dest_ip"],
        "process": ["process_name"],
    }
    
    for rel_type, fields in related_fields.items():
        if rel_type == entity_type:
            continue
        for field in fields:
            rel_df = query_df(
                case_id,
                f"""
                SELECT e.{field} AS value, COUNT(*) AS count
                FROM events e
                WHERE {base_where}
                  AND e.{field} IS NOT NULL
                  AND e.{field} != ''
                GROUP BY e.{field}
                ORDER BY count DESC
                LIMIT 10
                """,
                tuple(base_params),
            )
            if not rel_df.empty:
                related[f"{rel_type}_{field}"] = rel_df.to_dict("records")
    
    # Outcomes
    outcomes = query_df(
        case_id,
        f"""
        SELECT e.outcome, COUNT(*) AS count
        FROM events e
        WHERE {base_where}
          AND e.outcome IS NOT NULL
        GROUP BY e.outcome
        """,
        tuple(base_params),
    )
    
    return {
        "exists": True,
        "entity_type": entity_type,
        "entity_value": entity_value,
        "total_events": stats["total_events"],
        "source_count": stats["source_count"],
        "event_type_count": stats["event_type_count"],
        "first_seen": stats["first_seen"],
        "last_seen": stats["last_seen"],
        "event_types": event_types.to_dict("records"),
        "sources": sources.to_dict("records"),
        "time_distribution": time_dist.to_dict("records"),
        "related": related,
        "outcomes": outcomes.to_dict("records") if not outcomes.empty else [],
    }


def render_entity_column(summary: Dict[str, Any], column_key: str) -> None:
    """Render an entity summary in a column."""
    if not summary.get("exists"):
        st.warning(f"No data found for {summary['entity_type']}: {summary['entity_value']}")
        return
    
    st.markdown(f"### {summary['entity_type'].upper()}: {summary['entity_value']}")
    
    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Events", f"{summary['total_events']:,}")
    col2.metric("Event Types", summary["event_type_count"])
    
    col3, col4 = st.columns(2)
    col3.metric("Sources", summary["source_count"])
    
    # Time range
    if summary.get("first_seen") and summary.get("last_seen"):
        try:
            first = datetime.fromisoformat(summary["first_seen"].replace("Z", "+00:00"))
            last = datetime.fromisoformat(summary["last_seen"].replace("Z", "+00:00"))
            duration = last - first
            col4.metric("Duration", f"{duration.days}d {duration.seconds // 3600}h")
        except (ValueError, AttributeError):
            col4.metric("Duration", "N/A")
    
    st.caption(f"First: {summary.get('first_seen', 'N/A')}")
    st.caption(f"Last: {summary.get('last_seen', 'N/A')}")
    
    # Event types
    st.markdown("#### Top Event Types")
    if summary.get("event_types"):
        et_df = pd.DataFrame(summary["event_types"])
        st.dataframe(et_df, use_container_width=True, height=200)
    
    # Sources
    st.markdown("#### Sources")
    if summary.get("sources"):
        src_df = pd.DataFrame(summary["sources"])
        st.dataframe(src_df, use_container_width=True, height=100)
    
    # Outcomes
    if summary.get("outcomes"):
        st.markdown("#### Outcomes")
        out_df = pd.DataFrame(summary["outcomes"])
        st.dataframe(out_df, use_container_width=True, height=100)


def page_entity_diff(case_id: str) -> None:
    """Entity comparison/diff page."""
    st.subheader("Entity Comparison")
    
    st.markdown("""
    Compare two entities side-by-side to identify behavioral differences, 
    timeline overlaps, and anomalies. Useful for comparing compromised vs baseline entities.
    """)
    
    # Entity selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Entity A")
        type_a = st.selectbox("Type", ENTITY_TYPES, key="diff_type_a")
        options_a = entity_options(case_id, type_a)
        value_a = st.selectbox("Value", [""] + options_a, key="diff_value_a")
    
    with col2:
        st.markdown("#### Entity B")
        type_b = st.selectbox("Type", ENTITY_TYPES, key="diff_type_b", index=0)
        options_b = entity_options(case_id, type_b)
        value_b = st.selectbox("Value", [""] + options_b, key="diff_value_b")
    
    if not value_a or not value_b:
        st.info("Select two entities to compare.")
        return
    
    if value_a == value_b and type_a == type_b:
        st.warning("Please select two different entities to compare.")
        return
    
    # Load summaries
    with st.spinner("Loading entity data..."):
        summary_a = get_entity_summary(case_id, type_a, value_a)
        summary_b = get_entity_summary(case_id, type_b, value_b)
    
    # Side-by-side comparison
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        render_entity_column(summary_a, "a")
    
    with col2:
        render_entity_column(summary_b, "b")
    
    # Comparison insights
    st.markdown("---")
    st.markdown("### Comparison Insights")
    
    if summary_a.get("exists") and summary_b.get("exists"):
        # Event type overlap
        types_a = {et["event_type"] for et in summary_a.get("event_types", [])}
        types_b = {et["event_type"] for et in summary_b.get("event_types", [])}
        common_types = types_a & types_b
        unique_a = types_a - types_b
        unique_b = types_b - types_a
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Common Event Types", len(common_types))
        col2.metric(f"Unique to {value_a[:15]}", len(unique_a))
        col3.metric(f"Unique to {value_b[:15]}", len(unique_b))
        
        if unique_a:
            st.markdown(f"**Event types only in {value_a}:** {', '.join(list(unique_a)[:10])}")
        if unique_b:
            st.markdown(f"**Event types only in {value_b}:** {', '.join(list(unique_b)[:10])}")
        
        # Timeline overlap visualization
        st.markdown("#### Timeline Comparison")
        
        time_a = summary_a.get("time_distribution", [])
        time_b = summary_b.get("time_distribution", [])
        
        if time_a or time_b:
            # Combine into single dataframe for comparison
            df_a = pd.DataFrame(time_a)
            df_b = pd.DataFrame(time_b)
            
            if not df_a.empty:
                df_a["entity"] = value_a[:20]
            if not df_b.empty:
                df_b["entity"] = value_b[:20]
            
            combined = pd.concat([df_a, df_b], ignore_index=True)
            
            if not combined.empty:
                chart = alt.Chart(combined).mark_line(point=True).encode(
                    x=alt.X("hour:T", title="Time"),
                    y=alt.Y("count:Q", title="Events"),
                    color=alt.Color("entity:N", title="Entity"),
                    tooltip=["hour:T", "count:Q", "entity:N"],
                ).properties(height=300)
                
                st.altair_chart(chart, use_container_width=True)
        
        # Source overlap
        sources_a = {s["source_system"] for s in summary_a.get("sources", [])}
        sources_b = {s["source_system"] for s in summary_b.get("sources", [])}
        common_sources = sources_a & sources_b
        
        st.markdown(f"**Common sources:** {', '.join(common_sources) if common_sources else 'None'}")
        
        # Outcome comparison
        out_a = {o["outcome"]: o["count"] for o in summary_a.get("outcomes", [])}
        out_b = {o["outcome"]: o["count"] for o in summary_b.get("outcomes", [])}
        
        if out_a or out_b:
            st.markdown("#### Outcome Distribution")
            col1, col2 = st.columns(2)
            with col1:
                if out_a:
                    for outcome, count in out_a.items():
                        st.write(f"{outcome}: {count}")
            with col2:
                if out_b:
                    for outcome, count in out_b.items():
                        st.write(f"{outcome}: {count}")
