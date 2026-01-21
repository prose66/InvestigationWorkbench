from __future__ import annotations

import streamlit as st

from services.db import query_df, query_one


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
