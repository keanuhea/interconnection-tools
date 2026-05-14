"""FERC + PJM Interconnection RAG — Tapestry-narrative dashboard.

Companion to the operator simulator: that page simulates the queue's
structured data, this one queries the unstructured documents that govern
it. Two angles on the same fragmented-data problem.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from src.corpus.config import get_chroma_collection
from src.corpus.query import ask, retrieve

if st.button("← Back to cover"):
    st.switch_page("pages/0_Cover.py")


# ── Helpers ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _corpus_documents() -> list[dict]:
    """Return [{filename, chunks, label}] for every doc currently indexed."""
    try:
        collection = get_chroma_collection()
        existing = collection.get(include=["metadatas"])
    except Exception:
        return []
    counts: dict[str, int] = {}
    for m in existing.get("metadatas") or []:
        name = (m or {}).get("filename")
        if name:
            counts[name] = counts.get(name, 0) + 1
    docs = [
        {"filename": name, "chunks": n, "label": _pretty_label(name)}
        for name, n in sorted(counts.items())
    ]
    return docs


def _pretty_label(filename: str) -> str:
    stem = Path(filename).stem
    if stem.startswith("ferc_order_2023a"):
        return "FERC Order 2023-A (rehearing)"
    if stem.startswith("ferc_order_2023"):
        return "FERC Order 2023 (final rule)"
    if "interconnection-reform-progress" in stem:
        return "PJM: Interconnection Reform Progress (fact sheet)"
    if "generation-interconnection-fact" in stem:
        return "PJM: Generation Interconnection (fact sheet)"
    if "ab1092" in stem:
        return "PJM: Facility Study, queue AB1-092"
    return stem.replace("_", " ").replace("-", " ").title()


SUGGESTED_QUESTIONS = [
    "How does FERC Order 2023 change the cluster study process?",
    "What financial milestones must developers meet to maintain queue position?",
    "How are network upgrade costs allocated between projects in a cluster?",
    "What happens when a project withdraws after triggering studies?",
    "What did Order 2023-A change about the original rule?",
    "How is PJM implementing the cluster reform in its transition cycles?",
]


# ── State ────────────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ── Headline ─────────────────────────────────────────────────────────────────
st.title("The grid's rulebook is locked inside a thousand PDFs")
st.markdown(
    "FERC Order 2023, its rehearing order, PJM's tariff manuals, individual cluster "
    "study reports — the documents that govern how new generation connects to the grid "
    "live as un-queryable PDFs scattered across regulatory and operator sites. This "
    "dashboard is a small demo of what changes when you put a retrieval-augmented model "
    "on top of them."
)
st.caption(
    "Companion to the operator simulator (the structured-data side). "
    "Local embeddings retrieve relevant chunks · Claude Sonnet 4.6 synthesizes an "
    "answer with citations back to the source PDF and page."
)

st.divider()

# ── 1. Chat — primary surface, full width ────────────────────────────────────
# Replay history first so the conversation reads top-down.
for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn.get("citations"):
            with st.expander(f"Sources ({len(turn['citations'])})"):
                for c in turn["citations"]:
                    loc = f"p.{c.page}" if c.page else "page ?"
                    st.markdown(
                        f"**{_pretty_label(c.filename)}** · {loc} · "
                        f"similarity {c.score:.2f}"
                    )
                    st.caption(f"> {c.text}")

# Pick up the next question — chip click takes priority, otherwise chat input
incoming = st.session_state.pending_question
st.session_state.pending_question = None
if not incoming:
    incoming = st.chat_input(
        "Ask about FERC Order 2023, cluster studies, queue mechanics..."
    )

if incoming:
    st.session_state.history.append({"role": "user", "content": incoming})
    with st.chat_message("user"):
        st.markdown(incoming)

    has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    with st.chat_message("assistant"):
        if has_key:
            with st.spinner("Retrieving + generating..."):
                result = ask(incoming)
            answer_text = result.answer
            citations = result.citations
        else:
            with st.spinner("Retrieving (LLM disabled — no Anthropic key set)..."):
                citations = retrieve(incoming)
            answer_text = (
                "⚠️ `ANTHROPIC_API_KEY` isn't set, so I can't synthesize an answer. "
                "Below are the top retrieved chunks from the corpus — these are what "
                "would be sent to Claude for synthesis. Set the key in `.env` to enable "
                "full RAG answers."
            )
        st.markdown(answer_text)
        with st.expander(f"Sources ({len(citations)})", expanded=not has_key):
            for c in citations:
                loc = f"p.{c.page}" if c.page else "page ?"
                st.markdown(
                    f"**{_pretty_label(c.filename)}** · {loc} · "
                    f"similarity {c.score:.2f}"
                )
                st.caption(f"> {c.text}")
        st.session_state.history.append({
            "role": "assistant",
            "content": answer_text,
            "citations": citations,
        })


# ── 2. Suggested questions ───────────────────────────────────────────────────
st.divider()
st.subheader("Try a question")
st.caption("Click any to send it to the corpus:")
sq_cols = st.columns(2)
for i, q in enumerate(SUGGESTED_QUESTIONS):
    with sq_cols[i % 2]:
        if st.button(q, use_container_width=True, key=f"sq_{hash(q)}"):
            st.session_state.pending_question = q
            st.rerun()


# ── 3. Source documents ──────────────────────────────────────────────────────
st.divider()
st.subheader("Documents indexed")
docs = _corpus_documents()
if not docs:
    st.warning(
        "No documents indexed yet. From the repo root run:\n\n"
        "```\npython -m src.corpus.ingest\n```"
    )
else:
    total_chunks = sum(d["chunks"] for d in docs)
    st.caption(f"{len(docs)} documents · {total_chunks:,} chunks · embedded locally")
    doc_cols = st.columns(2)
    for i, d in enumerate(docs):
        with doc_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{d['label']}**")
                st.caption(f"`{d['filename']}` · {d['chunks']} chunks")


# ── Closing callout ──────────────────────────────────────────────────────────
st.divider()
st.info(
    "**Where this fits.** This is half of a pair. The operator simulator (other page) "
    "models the *structured* side of the same problem — a multi-state Markov simulation "
    "of queue progression with an interactive scenario panel. Tapestry's product surface "
    "unifies both: structured-data simulation for what-if planning, document understanding "
    "for the regulatory and engineering context that grounds the data."
)
st.caption(
    "Built with LlamaIndex + ChromaDB + Claude Sonnet 4.6 · local embeddings via "
    "BAAI/bge-small-en-v1.5 · source code: github.com/keanuhea/interconnection-tools"
)
