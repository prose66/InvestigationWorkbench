from __future__ import annotations

import sqlite3
import streamlit as st

from services.db import db_path, query_df, table_exists


def page_bookmarks(case_id: str) -> None:
    """Page for viewing and managing bookmarked events."""
    st.subheader("Bookmarks")
    if not table_exists(case_id, "bookmarked_events"):
        st.info("No bookmarks table found. Bookmark events from the Timeline Explorer.")
        return

    bookmarks_df = query_df(
        case_id,
        """
        SELECT b.bookmark_id, b.event_pk, b.label, b.notes, b.created_at,
               e.event_ts, e.source_system, e.event_type, e.host, e.user, e.message
        FROM bookmarked_events b
        JOIN events e ON b.event_pk = e.event_pk
        WHERE b.case_id = ?
        ORDER BY e.event_ts DESC
        """,
        (case_id,),
    )
    if bookmarks_df.empty:
        st.info("No bookmarked events yet. Use the Timeline Explorer to bookmark events.")
        return

    st.metric("Bookmarked Events", len(bookmarks_df))
    st.dataframe(
        bookmarks_df[
            [
                "event_ts",
                "source_system",
                "event_type",
                "host",
                "user",
                "message",
                "label",
            ]
        ],
        use_container_width=True,
    )

    def format_bookmark(bid: int) -> str:
        row = bookmarks_df[bookmarks_df["bookmark_id"] == bid].iloc[0]
        return f"{row['event_ts']} - {row['event_type']}"

    selected_bookmark = st.selectbox(
        "Select bookmark to edit",
        bookmarks_df["bookmark_id"].tolist(),
        format_func=format_bookmark,
    )
    selected_row = bookmarks_df[bookmarks_df["bookmark_id"] == selected_bookmark].iloc[0]

    new_label = st.text_input("Label", value=selected_row.get("label") or "", key="bookmark_label")
    new_notes = st.text_area("Notes", value=selected_row.get("notes") or "", key="bookmark_notes", height=100)

    col1, col2 = st.columns(2)
    if col1.button("Save"):
        with sqlite3.connect(db_path(case_id)) as conn:
            conn.execute(
                "UPDATE bookmarked_events SET label = ?, notes = ? WHERE bookmark_id = ?",
                (new_label, new_notes, selected_bookmark),
            )
        st.success("Bookmark updated.")
    if col2.button("Delete"):
        with sqlite3.connect(db_path(case_id)) as conn:
            conn.execute("DELETE FROM bookmarked_events WHERE bookmark_id = ?", (selected_bookmark,))
        st.success("Bookmark deleted.")
        st.rerun()
