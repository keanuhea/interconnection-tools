"""FERC + PJM Interconnection RAG — Tapestry-narrative dashboard.

Companion to the operator simulator: that page simulates the queue's
structured data, this one queries the unstructured documents that govern
it. Two angles on the same fragmented-data problem.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from src.corpus.config import PDF_DIR, get_chroma_collection
from src.corpus.query import ask, retrieve

st.set_page_config(
    page_title="Document corpus · Interconnection tools",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner="Building corpus index (first-time setup, ~30s)...")
def _ensure_corpus_index() -> str | None:
    """Build the index on first session if it's empty.

    Idempotent — `ingest()` checks what's already indexed and skips dupes.
    Returns an error string for display, or None on success/no-op.
    Auto-rebuilding here avoids ChromaDB version-mismatch issues between
    the committed index and the deployment's chromadb wheel.
    """
    try:
        if not PDF_DIR.exists() or not any(PDF_DIR.glob("*.pdf")):
            return None
        collection = get_chroma_collection()
        if collection.count() > 0:
            return None
        from src.corpus.ingest import ingest
        ingest()
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    return None


_ingest_error = _ensure_corpus_index()

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

# ── 1. Ask the corpus — sample-question expander, then inline text input ────
incoming = st.session_state.pending_question
st.session_state.pending_question = None

with st.expander("💡 Try a question", expanded=False):
    st.caption("Click any to send it to the corpus:")
    sq_cols = st.columns(2)
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        with sq_cols[i % 2]:
            if st.button(q, use_container_width=True, key=f"sq_{hash(q)}"):
                st.session_state.pending_question = q
                st.rerun()

with st.form("query_form", clear_on_submit=True):
    typed = st.text_input(
        "Ask the corpus",
        placeholder="Ask about FERC Order 2023, cluster studies, queue mechanics...",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Send", type="primary")

if submitted and typed:
    incoming = typed

if incoming:
    has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    answer_text = None
    citations = []
    try:
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
    except (RuntimeError, ImportError, ModuleNotFoundError, TypeError) as e:
        # Empty corpus OR a vector-store dependency that didn't load cleanly
        # (e.g. chromadb on a too-new Python). Degrade gracefully.
        answer_text = (
            "📚 **The document corpus isn't indexed yet on this deployment.**\n\n"
            "The vector store is empty or its dependencies didn't load. "
            "Drop FERC/PJM PDFs into `data/pdfs/` and run "
            "`python -m src.corpus.ingest` to populate the index, then redeploy. "
            f"\n\n_Underlying error: `{type(e).__name__}: {e}`_"
        )
        citations = []
    st.session_state.history.insert(0, {
        "question": incoming,
        "answer": answer_text,
        "citations": citations,
        "had_key": has_key,
    })

# Render history (most-recent first)
for i, turn in enumerate(st.session_state.history):
    with st.container(border=True):
        st.markdown(f"**Q.** {turn['question']}")
        st.markdown(turn["answer"])
        if turn.get("citations"):
            with st.expander(
                f"Sources ({len(turn['citations'])})",
                expanded=(i == 0 and not turn.get("had_key", True)),
            ):
                for c in turn["citations"]:
                    loc = f"p.{c.page}" if c.page else "page ?"
                    st.markdown(
                        f"**{_pretty_label(c.filename)}** · {loc} · "
                        f"similarity {c.score:.2f}"
                    )
                    st.caption(f"> {c.text}")


# ── 2. Source documents ──────────────────────────────────────────────────────
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
