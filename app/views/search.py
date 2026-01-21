"""Search results view."""
from __future__ import annotations

import streamlit as st

from services.search import count_search_results, search_events
from state import queue_entity_navigation, queue_timeline_pivot


def page_search_results(case_id: str) -> None:
    """Display search results page."""
    st.subheader("Search Results")
    
    keyword = st.session_state.get("global_search_keyword", "")
    if not keyword:
        st.info("Enter a search term in the sidebar to search across all events.")
        return
    
    st.markdown(f"**Searching for:** `{keyword}`")
    
    total_count = count_search_results(case_id, keyword)
    if total_count == 0:
        st.warning("No events match your search.")
        return
    
    st.metric("Matching Events", total_count)
    
    limit = st.selectbox("Results to show", [50, 100, 200, 500], index=1)
    results_df = search_events(case_id, keyword, limit=limit)
    
    if results_df.empty:
        st.warning("No results found.")
        return
    
    # Display results table
    st.dataframe(
        results_df[[
            "event_ts", "source_system", "event_type", "host", "user",
            "src_ip", "dest_ip", "process_name", "outcome", "severity", "message"
        ]],
        use_container_width=True,
        height=400,
    )
    
    # Quick actions for selected result
    st.markdown("#### Quick Actions")
    selected_pk = st.selectbox(
        "Select an event to inspect",
        results_df["event_pk"].tolist(),
        format_func=lambda pk: f"{results_df[results_df['event_pk'] == pk].iloc[0]['event_ts']} - {results_df[results_df['event_pk'] == pk].iloc[0]['event_type']}"
    )
    
    selected = results_df[results_df["event_pk"] == selected_pk].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    if selected.get("host") and col1.button(f"Pivot to Host: {selected['host']}", key="pivot_host"):
        queue_timeline_pivot("host", selected["host"])
        st.rerun()
    
    if selected.get("user") and col2.button(f"Pivot to User: {selected['user']}", key="pivot_user"):
        queue_timeline_pivot("user", selected["user"])
        st.rerun()
    
    if selected.get("src_ip") and col3.button(f"Pivot to IP: {selected['src_ip']}", key="pivot_ip"):
        queue_timeline_pivot("ip", selected["src_ip"])
        st.rerun()
    
    # Show message/details
    st.markdown("#### Event Details")
    st.json(selected.to_dict())
