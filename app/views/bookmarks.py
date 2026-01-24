from __future__ import annotations

import sqlite3
import streamlit as st

from services.db import db_path, query_df, table_exists


def page_bookmarks(case_id: str) -> None:
    """Page for viewing and managing bookmarked events."""
    st.subheader("Bookmarks")
    st.caption("Events you've marked as important during your investigation")

    if not table_exists(case_id, "bookmarked_events"):
        st.info("No bookmarks yet. Use the Timeline Explorer to bookmark important events.")
        return

    bookmarks_df = query_df(
        case_id,
        """
        SELECT b.bookmark_id, b.event_pk, b.label, b.notes, b.created_at,
               e.event_ts, e.source_system, e.event_type, e.host, e.user, e.message, e.severity
        FROM bookmarked_events b
        JOIN events e ON b.event_pk = e.event_pk
        WHERE b.case_id = ?
        ORDER BY e.event_ts DESC
        """,
        (case_id,),
    )
    if bookmarks_df.empty:
        st.info("No bookmarked events yet. Use the Timeline Explorer to bookmark important events.")
        return

    # Summary metrics
    col1, col2, col3 = st.columns([2, 2, 1])
    col1.metric("Total Bookmarks", len(bookmarks_df))
    col2.metric("Unique Hosts", bookmarks_df["host"].nunique())
    with col3:
        st.download_button(
            "Export CSV",
            data=bookmarks_df.to_csv(index=False),
            file_name=f"{case_id}_bookmarks.csv",
            mime="text/csv",
            key="export_bookmarks_csv",
        )

    st.markdown("---")

    # Bookmarks table
    st.markdown("#### Bookmarked Events")
    st.dataframe(
        bookmarks_df[
            [
                "event_ts",
                "source_system",
                "event_type",
                "host",
                "user",
                "severity",
                "message",
                "label",
            ]
        ],
        use_container_width=True,
    )

    st.markdown("---")

    # Edit section
    st.markdown("#### Edit Bookmark")

    def format_bookmark(bid: int) -> str:
        row = bookmarks_df[bookmarks_df["bookmark_id"] == bid].iloc[0]
        label = row.get("label") or "Unlabeled"
        return f"{row['event_ts'][:16]} - {row['event_type']} ({label})"

    selected_bookmark = st.selectbox(
        "Select bookmark",
        bookmarks_df["bookmark_id"].tolist(),
        format_func=format_bookmark,
    )
    selected_row = bookmarks_df[bookmarks_df["bookmark_id"] == selected_bookmark].iloc[0]

    edit_col1, edit_col2 = st.columns(2)
    with edit_col1:
        new_label = st.text_input(
            "Label",
            value=selected_row.get("label") or "",
            key="bookmark_label",
            placeholder="e.g., Initial access, Lateral movement",
        )
    with edit_col2:
        st.caption(f"Event: {selected_row['event_type']}")
        st.caption(f"Host: {selected_row['host'] or 'N/A'}")

    new_notes = st.text_area(
        "Investigation Notes",
        value=selected_row.get("notes") or "",
        key="bookmark_notes",
        height=100,
        placeholder="Add your analysis notes here...",
    )

    action_col1, action_col2, action_col3 = st.columns([1, 1, 3])
    with action_col1:
        if st.button("Save Changes", type="primary"):
            with sqlite3.connect(db_path(case_id)) as conn:
                conn.execute(
                    "UPDATE bookmarked_events SET label = ?, notes = ? WHERE bookmark_id = ?",
                    (new_label, new_notes, selected_bookmark),
                )
            st.success("Bookmark updated.")
            st.rerun()
    with action_col2:
        if st.button("Delete Bookmark"):
            with sqlite3.connect(db_path(case_id)) as conn:
                conn.execute("DELETE FROM bookmarked_events WHERE bookmark_id = ?", (selected_bookmark,))
            st.success("Bookmark deleted.")
            st.rerun()
