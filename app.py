"""Cover page for interconnection-tools.

Two dashboards, one front door. Uses Streamlit's modern st.navigation() API
so the cover lives at app.py and each tool is a navigable page. The sidebar
nav is suppressed in favor of the cover-page CTAs.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Interconnection tools",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Page registry ────────────────────────────────────────────────────────────
cover = st.Page("pages/0_Cover.py", title="Cover", icon="📊", default=True)
operator = st.Page(
    "pages/1_Operator_view.py",
    title="Operator simulator",
    icon="⚡",
)
corpus = st.Page(
    "pages/2_Document_corpus.py",
    title="Document corpus",
    icon="📚",
)

navigation = st.navigation([cover, operator, corpus], position="hidden")
navigation.run()
