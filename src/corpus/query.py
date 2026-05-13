"""Query the vector store.

Two entry points:

- `retrieve(question)` — embeds the question locally, returns top-k chunks.
  Free, no API key required. Useful for sanity-checking the index and for
  gracefully degrading the UI when Anthropic isn't configured.
- `ask(question)` — full RAG: retrieve + Claude generation with citations.
  Requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.corpus.config import (
    TOP_K,
    configure_embeddings_only,
    configure_llama_index,
    get_chroma_collection,
)


@dataclass
class Citation:
    filename: str
    page: int | None
    score: float
    text: str


@dataclass
class Answer:
    question: str
    answer: str
    citations: list[Citation]


def _load_index():
    from llama_index.core import StorageContext, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore

    collection = get_chroma_collection()
    if collection.count() == 0:
        raise RuntimeError(
            "Vector store is empty. Run `python -m src.ingest` first."
        )
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context
    )


def retrieve(question: str, top_k: int = TOP_K) -> list[Citation]:
    """Embed the question locally and return the top-k matching chunks.

    No LLM call — pure retrieval. Useful when you want to inspect what the
    index would surface for a question, or when the Anthropic key isn't set.
    """
    from llama_index.core import StorageContext, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore

    configure_embeddings_only()
    collection = get_chroma_collection()
    if collection.count() == 0:
        raise RuntimeError("Vector store is empty. Run `python -m src.ingest` first.")

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(question)

    return [
        Citation(
            filename=(n.node.metadata or {}).get("filename", "unknown"),
            page=(n.node.metadata or {}).get("page_label")
                 or (n.node.metadata or {}).get("page"),
            score=float(n.score) if n.score is not None else 0.0,
            text=n.node.get_content()[:600],
        )
        for n in nodes
    ]


def ask(question: str, top_k: int = TOP_K) -> Answer:
    """Run a single RAG query and return the answer plus citations."""
    configure_llama_index()
    index = _load_index()

    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        response_mode="compact",
    )
    response = query_engine.query(question)

    citations: list[Citation] = []
    for node in response.source_nodes:
        meta = node.node.metadata or {}
        citations.append(
            Citation(
                filename=meta.get("filename", "unknown"),
                page=meta.get("page_label") or meta.get("page"),
                score=float(node.score) if node.score is not None else 0.0,
                text=node.node.get_content()[:400],
            )
        )

    return Answer(question=question, answer=str(response), citations=citations)


def format_citations(citations: list[Citation]) -> str:
    lines = []
    for i, c in enumerate(citations, 1):
        loc = f"p.{c.page}" if c.page else "page ?"
        lines.append(f"  [{i}] {c.filename} ({loc}, score={c.score:.3f})")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "How does FERC Order 2023 change the cluster study process?"
    result = ask(q)
    print(f"Q: {result.question}\n")
    print(f"A: {result.answer}\n")
    print("Sources:")
    print(format_citations(result.citations))
