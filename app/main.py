from __future__ import annotations

import streamlit as st

from views.ask_ai import page_ask_ai
from views.bookmarks import page_bookmarks
from views.entity import page_entity_page
from views.entity_diff import page_entity_diff
from views.entity_graph import page_entity_graph
from views.overview import page_case_overview
from views.search import page_search_results
from views.swimlane import page_swimlane_timeline
from views.timeline import page_timeline
from services.db import list_cases

FEATURE_ENTITY_EXPLORER = False


def main() -> None:
    st.set_page_config(page_title="Investigation Workbench", layout="wide")
    st.title("Investigation Workbench")

    cases = list_cases()
    if not cases:
        st.warning("No cases found. Run `python -m cli init-case <case_id>` first.")
        return

    case_id = st.sidebar.selectbox("Case", cases)
    
    # Global search
    st.sidebar.markdown("---")
    search_keyword = st.sidebar.text_input(
        "🔍 Search Events",
        value=st.session_state.get("global_search_keyword", ""),
        placeholder="Search across all events...",
        key="global_search_input",
    )
    if search_keyword != st.session_state.get("global_search_keyword", ""):
        st.session_state["global_search_keyword"] = search_keyword
        if search_keyword:
            st.session_state["selected_page"] = "Search Results"
            st.rerun()
    st.sidebar.markdown("---")
    
    next_page = st.session_state.pop("next_page", None)
    if next_page:
        st.session_state["selected_page"] = next_page

    pages = {
        "Case Overview": page_case_overview,
        "Timeline Explorer": page_timeline,
        "Swimlane Timeline": page_swimlane_timeline,
        "Entity Page": page_entity_page,
        "Entity Graph": page_entity_graph,
        "Entity Comparison": page_entity_diff,
        "Bookmarks": page_bookmarks,
        "Search Results": page_search_results,
        "Ask AI (Stub)": page_ask_ai,
    }

    if FEATURE_ENTITY_EXPLORER:
        from views.entity_explorer import page_entity_explorer

        pages["Entity Explorer"] = page_entity_explorer

    page = st.sidebar.radio("Page", list(pages.keys()), key="selected_page")
    pages[page](case_id)


if __name__ == "__main__":
    main()
