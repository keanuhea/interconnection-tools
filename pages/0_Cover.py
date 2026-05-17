"""Cover page — the front door for both dashboards.

Frames the unified narrative and surfaces two prominent CTAs. The visitor
either clicks into the operator simulator or the document corpus.
"""

from __future__ import annotations

import streamlit as st

st.title("The U.S. grid is stuck waiting in line")
st.markdown(
    "Roughly **2,800 GW** of new generation capacity is currently sitting in U.S. "
    "interconnection queues — about **1.6× the entire installed capacity** of the grid "
    "today. Most of it never gets built. Only ~17% of resolved interconnection requests "
    "have historically reached commercial operation."
)
st.markdown(
    "The data problem is fragmented across two layers — and so is this toolkit."
)

st.divider()

c1, c2 = st.columns(2, gap="large")

with c1:
    st.subheader("⚡ Operator simulator")
    st.markdown(
        "The **structured** side. A multi-state survival model of how today's "
        "22,000 active LBNL projects move through the queue, with an interactive "
        "scenario panel that lets you pull three operator-side levers — cluster "
        "study throughput, withdrawal strictness, construction speed — and see "
        "the resulting fan chart, KPI deltas, and Claude-written executive brief."
    )
    st.markdown(
        "**Built from:** Berkeley Lab *Queued Up* 2025 dataset · live PJM queue API · "
        "10-year forward Monte Carlo · 500 replicates per scenario."
    )
    if st.button("Open the operator simulator →", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Operator_view.py")

with c2:
    st.subheader("📚 Document corpus")
    st.markdown(
        "The **unstructured** side. The rules governing the queue — FERC Order 2023, "
        "its rehearing order, PJM's tariff manuals, individual cluster study reports — "
        "live as un-queryable PDFs. This dashboard wraps the corpus in a "
        "retrieval-augmented chat interface with inline citations to source PDF and page."
    )
    st.markdown(
        "**Built from:** local sentence-transformers embeddings · ChromaDB · "
        "Claude Sonnet 4.6 synthesis · 5 seed PDFs (~600 pages, 3,000 chunks)."
    )
    if st.button("Open the document corpus →", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Document_corpus.py")

st.divider()

with st.expander("Why two dashboards instead of one"):
    st.markdown(
        """
The interconnection process is a *fragmented* data problem. Two distinct fragments:

| Layer | What it is | What you'd ask it |
|---|---|---|
| **Structured** | Tabular data — queue rosters, milestone dates, project attributes | "If FERC reform delivers, how much more capacity reaches the grid by 2030?" |
| **Unstructured** | PDF documents — FERC orders, tariff manuals, cluster study reports | "How does Order 2023-A change cost allocation in clusters?" |

A real operator workflow stitches both. These two dashboards are a small,
public-data demonstration of how the structured and unstructured layers fit
together — the same two-sided data problem that vendors building unified
grid-operator platforms (Tapestry/Alphabet, WeaveGrid, Wattch, others) are
working on at the operator-internal level.

**Source repos:**
- [`interconnection-queue-analysis`](https://github.com/keanuhea/interconnection-queue-analysis) — the operator simulator, standalone
- [`ferc-pjm-rag`](https://github.com/keanuhea/ferc-pjm-rag) — the document corpus, standalone
- [`interconnection-tools`](https://github.com/keanuhea/interconnection-tools) — this combined dashboard
"""
    )

st.caption(
    "Built with pandas + scikit-learn + plotly + streamlit + LlamaIndex + ChromaDB + "
    "Claude Sonnet 4.6 · keanuhea.parker@gmail.com"
)
