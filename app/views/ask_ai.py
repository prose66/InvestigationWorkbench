from __future__ import annotations

import streamlit as st


def page_ask_ai(case_id: str) -> None:
    st.subheader("Ask AI (Stub)")
    question = st.text_input("Question")
    if not question:
        st.info("Ask a question to see the suggested SQL.")
        return

    st.markdown("### Suggested SQL")
    suggested_sql = """
SELECT event_type, COUNT(*) AS count
FROM events
WHERE case_id = ?
GROUP BY event_type
ORDER BY count DESC
"""
    st.code(suggested_sql.strip(), language="sql")
    st.markdown("### Suggested Visualization")
    st.write("bar chart")
    st.caption("This is a placeholder. Wire in your LLM provider to generate SQL safely.")
