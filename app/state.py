from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st


def queue_page_navigation(page_name: str) -> None:
    st.session_state["next_page"] = page_name


# --- Multi-Entity Pivot Support ---

ENTITY_COLUMN_MAP = {
    "host": "host",
    "user": "user",
    "ip": "src_ip",
    "hash": "file_hash",
    "process": "process_name",
}


def get_pivot_entities() -> List[Dict[str, str]]:
    """Get the current list of pivot entities."""
    return st.session_state.get("pivot_entities", [])


def add_pivot_entity(entity_type: str, entity_value: str) -> None:
    """Add a pivot entity to the current filter chain (AND logic).

    Args:
        entity_type: Type of entity (host, user, ip, hash, process)
        entity_value: Value of the entity
    """
    column = ENTITY_COLUMN_MAP.get(entity_type)
    if not column:
        return

    pivot_entities = get_pivot_entities()
    new_entity = {"column": column, "value": entity_value, "type": entity_type}

    # Avoid duplicates
    for existing in pivot_entities:
        if existing["column"] == column and existing["value"] == entity_value:
            return

    pivot_entities.append(new_entity)
    st.session_state["pivot_entities"] = pivot_entities


def remove_pivot_entity(index: int) -> None:
    """Remove a pivot entity by index."""
    pivot_entities = get_pivot_entities()
    if 0 <= index < len(pivot_entities):
        pivot_entities.pop(index)
        st.session_state["pivot_entities"] = pivot_entities


def clear_pivot_entities() -> None:
    """Clear all pivot entities."""
    st.session_state["pivot_entities"] = []


def set_pivot_entity_single(entity_type: str, entity_value: str) -> None:
    """Set a single pivot entity, replacing any existing pivots.

    Use this when you want to view ONLY events for this entity,
    not the intersection with previous pivots.
    """
    column = ENTITY_COLUMN_MAP.get(entity_type)
    if column:
        st.session_state["pivot_entities"] = [
            {"column": column, "value": entity_value, "type": entity_type}
        ]


def set_timeline_pivot(entity_type: str, entity_value: str) -> None:
    """Legacy function - now adds to pivot chain instead of replacing."""
    add_pivot_entity(entity_type, entity_value)


def queue_entity_navigation(entity_type: str, entity_value: str) -> None:
    st.session_state["active_entity"] = {"type": entity_type, "value": entity_value}
    queue_page_navigation("Entity Page")


def queue_timeline_pivot(entity_type: str, entity_value: str) -> None:
    """Add entity to pivot chain and navigate to Timeline Explorer."""
    add_pivot_entity(entity_type, entity_value)
    queue_page_navigation("Timeline Explorer")


def queue_timeline_pivot_single(entity_type: str, entity_value: str) -> None:
    """Replace pivot chain with single entity and navigate to Timeline Explorer."""
    set_pivot_entity_single(entity_type, entity_value)
    queue_page_navigation("Timeline Explorer")


def queue_timeline_filter(filter_type: str, filter_value: str) -> None:
    """Queue a filter for the Timeline Explorer.

    Args:
        filter_type: Type of filter (source_system, event_type)
        filter_value: Value to filter by
    """
    st.session_state["timeline_filter"] = {"type": filter_type, "value": filter_value}
    queue_page_navigation("Timeline Explorer")


# --- Filter Persistence ---

def _filter_key(case_id: str, page: str) -> str:
    """Generate a case-scoped key for filter state."""
    return f"filters:{case_id}:{page}"


def get_filter_state(case_id: str, page: str = "timeline") -> Dict[str, Any]:
    """Get persisted filter state for a page."""
    key = _filter_key(case_id, page)
    return st.session_state.get(key, {})


def save_filter_state(case_id: str, page: str, filters: Dict[str, Any]) -> None:
    """Save filter state for a page."""
    key = _filter_key(case_id, page)
    st.session_state[key] = filters


def clear_filter_state(case_id: str, page: str = "timeline") -> None:
    """Clear persisted filter state for a page."""
    key = _filter_key(case_id, page)
    if key in st.session_state:
        del st.session_state[key]


# --- Navigation History ---

MAX_HISTORY_ENTRIES = 20


def _history_key() -> str:
    return "nav_history"


def get_navigation_history() -> List[Dict[str, Any]]:
    """Get navigation history."""
    return st.session_state.get(_history_key(), [])


def push_navigation(page: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Push a page to navigation history."""
    history = get_navigation_history()
    entry = {"page": page, "context": context or {}}
    # Avoid duplicating the current page at the top
    if history and history[-1]["page"] == page:
        history[-1] = entry
    else:
        history.append(entry)
    # Trim to max entries
    if len(history) > MAX_HISTORY_ENTRIES:
        history = history[-MAX_HISTORY_ENTRIES:]
    st.session_state[_history_key()] = history


def pop_navigation() -> Optional[Dict[str, Any]]:
    """Pop the last navigation entry."""
    history = get_navigation_history()
    if len(history) > 1:
        history.pop()  # Remove current
        st.session_state[_history_key()] = history
        return history[-1] if history else None
    return None


def get_breadcrumbs(limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent breadcrumbs for display."""
    history = get_navigation_history()
    return history[-limit:]
