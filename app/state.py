from __future__ import annotations

import streamlit as st


def queue_page_navigation(page_name: str) -> None:
    st.session_state["next_page"] = page_name


def set_timeline_pivot(entity_type: str, entity_value: str) -> None:
    column_map = {
        "host": "host",
        "user": "user",
        "ip": "src_ip",
        "hash": "file_hash",
        "process": "process_name",
    }
    column = column_map.get(entity_type)
    if column:
        st.session_state["timeline_pivot"] = {"column": column, "value": entity_value}


def queue_entity_navigation(entity_type: str, entity_value: str) -> None:
    st.session_state["active_entity"] = {"type": entity_type, "value": entity_value}
    queue_page_navigation("Entity Page")


def queue_timeline_pivot(entity_type: str, entity_value: str) -> None:
    set_timeline_pivot(entity_type, entity_value)
    queue_page_navigation("Timeline Explorer")


def queue_timeline_filter(filter_type: str, filter_value: str) -> None:
    """Queue a filter for the Timeline Explorer.
    
    Args:
        filter_type: Type of filter (source_system, event_type)
        filter_value: Value to filter by
    """
    st.session_state["timeline_filter"] = {"type": filter_type, "value": filter_value}
    queue_page_navigation("Timeline Explorer")
