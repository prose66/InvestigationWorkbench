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
from state import get_breadcrumbs, push_navigation, pop_navigation

FEATURE_ENTITY_EXPLORER = False

# Custom CSS for styling
CUSTOM_CSS = """
<style>
/* Reduce default padding */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* Sidebar section spacing */
.sidebar .element-container {
    margin-bottom: 0.25rem;
}

/* Table row hover effects */
.stDataFrame tbody tr:hover {
    background-color: rgba(31, 119, 180, 0.1);
}

/* Severity color classes */
.severity-high {
    color: #d32f2f;
    font-weight: 600;
}
.severity-medium {
    color: #f57c00;
    font-weight: 500;
}
.severity-low {
    color: #388e3c;
}

/* Gap alert styling */
.gap-alert-high {
    border-left: 4px solid #d32f2f;
    padding-left: 0.5rem;
}
.gap-alert-medium {
    border-left: 4px solid #f57c00;
    padding-left: 0.5rem;
}
.gap-alert-low {
    border-left: 4px solid #9e9e9e;
    padding-left: 0.5rem;
}

/* Navigation group styling */
.nav-group-header {
    font-size: 0.75rem;
    font-weight: 600;
    color: #666;
    margin-top: 0.5rem;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Breadcrumb styling */
.breadcrumb {
    font-size: 0.8rem;
    color: #666;
    margin-bottom: 0.5rem;
}
.breadcrumb a {
    color: #1f77b4;
    text-decoration: none;
}
.breadcrumb a:hover {
    text-decoration: underline;
}

/* Compact buttons in pagination */
.stButton > button {
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
}

/* Entity pivot buttons */
.pivot-btn {
    font-size: 0.75rem;
    padding: 0.15rem 0.3rem;
}

/* Pivot filter chip styling */
.pivot-chip {
    display: inline-block;
    background-color: #e3f2fd;
    border: 1px solid #1976d2;
    border-radius: 16px;
    padding: 0.25rem 0.75rem;
    margin: 0.25rem;
    font-size: 0.85rem;
}

/* Card-like containers */
.card-container {
    background-color: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

/* Entity selector highlight */
.entity-selector {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

/* Metric card styling */
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    padding: 1rem;
    color: white;
}

/* Section dividers */
.section-divider {
    border-top: 1px solid #e0e0e0;
    margin: 1.5rem 0;
}

/* Compact info boxes */
div[data-testid="stAlert"] {
    padding: 0.5rem 1rem;
    margin-bottom: 0.5rem;
}

/* Better button spacing for filter chips */
div.row-widget.stButton {
    margin-bottom: 0.25rem;
}
</style>
"""

# Page groupings for navigation
PAGE_GROUPS = {
    "Investigation": [
        ("Case Overview", page_case_overview),
        ("Timeline Explorer", page_timeline),
        ("Swimlane Timeline", page_swimlane_timeline),
        ("Bookmarks", page_bookmarks),
        ("Search Results", page_search_results),
    ],
    "Entities": [
        ("Entity Page", page_entity_page),
        ("Entity Graph", page_entity_graph),
        ("Entity Comparison", page_entity_diff),
    ],
    "Tools": [
        ("Ask AI (Stub)", page_ask_ai),
    ],
}


def get_all_pages() -> dict:
    """Flatten page groups into a single dict."""
    pages = {}
    for group_pages in PAGE_GROUPS.values():
        for name, func in group_pages:
            pages[name] = func
    return pages


def render_breadcrumbs() -> None:
    """Render navigation breadcrumbs."""
    breadcrumbs = get_breadcrumbs(limit=4)
    if len(breadcrumbs) > 1:
        crumb_parts = []
        for i, crumb in enumerate(breadcrumbs[:-1]):
            crumb_parts.append(crumb["page"])
        crumb_parts.append(breadcrumbs[-1]["page"])
        st.caption(" > ".join(crumb_parts))


def main() -> None:
    st.set_page_config(page_title="Investigation Workbench", layout="wide")

    # Inject custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("Investigation Workbench")

    cases = list_cases()
    if not cases:
        st.warning("No cases found. Run `python -m cli init-case <case_id>` first.")
        return

    case_id = st.sidebar.selectbox("Case", cases)

    # Global search
    st.sidebar.markdown("---")
    search_keyword = st.sidebar.text_input(
        "Search Events",
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

    pages = get_all_pages()

    if FEATURE_ENTITY_EXPLORER:
        from views.entity_explorer import page_entity_explorer
        pages["Entity Explorer"] = page_entity_explorer
        PAGE_GROUPS["Entities"].append(("Entity Explorer", page_entity_explorer))

    # Grouped navigation
    st.sidebar.markdown("### Navigation")

    # Get current selection
    current_page = st.session_state.get("selected_page", "Case Overview")
    if current_page not in pages:
        current_page = "Case Overview"

    # Find which group the current page is in
    current_group = None
    for group_name, group_pages in PAGE_GROUPS.items():
        for page_name, _ in group_pages:
            if page_name == current_page:
                current_group = group_name
                break
        if current_group:
            break

    # Group selector
    group_names = list(PAGE_GROUPS.keys())
    selected_group_idx = group_names.index(current_group) if current_group else 0
    selected_group = st.sidebar.radio(
        "Section",
        group_names,
        index=selected_group_idx,
        key="nav_group",
        horizontal=True,
    )

    # Page selector within group
    group_page_names = [name for name, _ in PAGE_GROUPS[selected_group]]

    # If switching groups, select first page in new group
    if current_page not in group_page_names:
        current_page = group_page_names[0]
        st.session_state["selected_page"] = current_page

    page_idx = group_page_names.index(current_page) if current_page in group_page_names else 0
    selected_page = st.sidebar.radio(
        "Page",
        group_page_names,
        index=page_idx,
        key="selected_page",
    )

    # Track navigation history
    push_navigation(selected_page)

    # Back button
    breadcrumbs = get_breadcrumbs(limit=5)
    if len(breadcrumbs) > 1:
        bcol1, bcol2 = st.columns([1, 10])
        with bcol1:
            if st.button("Back", key="nav_back"):
                prev = pop_navigation()
                if prev:
                    st.session_state["selected_page"] = prev["page"]
                    st.rerun()
        with bcol2:
            render_breadcrumbs()
    else:
        render_breadcrumbs()

    # Render selected page
    pages[selected_page](case_id)


if __name__ == "__main__":
    main()
