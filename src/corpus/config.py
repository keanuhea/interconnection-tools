"""Shared config: paths, model names, and LlamaIndex Settings wiring.

Design choice: embeddings are computed locally via a small sentence-transformers
model (BAAI/bge-small-en-v1.5, 384-dim, ~130MB). That means anyone can clone
this repo and run `python -m src.ingest` without any API key. Generation uses
Claude Sonnet 4.6 via the Anthropic API — but only at query time, so the
expensive part (indexing the corpus) is free.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "ferc_pjm"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K = 5

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def configure_embeddings_only() -> None:
    """Wire local embeddings + chunker. No API key required.

    Used by the ingest pipeline so the corpus can be indexed for free.
    """
    from llama_index.core import Settings
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
    Settings.node_parser = SentenceSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )


def configure_llama_index() -> None:
    """Wire embeddings + Claude generation. Anthropic key required.

    Used by the query pipeline. Embeddings stay local; only the answer
    generation hits the API, so cost scales with how many questions you ask.
    """
    from llama_index.core import Settings
    from llama_index.llms.anthropic import Anthropic

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to .env in the project root. "
            "Indexing works without it, but answering questions needs the key."
        )

    configure_embeddings_only()
    Settings.llm = Anthropic(model=ANTHROPIC_MODEL)


def get_chroma_collection():
    """Return a persistent Chroma collection, creating it if needed."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(COLLECTION_NAME)
