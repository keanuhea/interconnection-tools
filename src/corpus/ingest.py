"""Ingest PDFs from data/pdfs/ into the persistent Chroma vector store.

Idempotent: each document's filename is recorded as metadata; documents already
present in the collection are skipped on re-run. To force re-ingest of a single
PDF, delete its chunks from Chroma or wipe the chroma_db/ directory.
"""

from __future__ import annotations

from pathlib import Path

from src.corpus.config import (
    PDF_DIR,
    configure_embeddings_only,
    get_chroma_collection,
)


def ingested_filenames(collection) -> set[str]:
    existing = collection.get(include=["metadatas"])
    metas = existing.get("metadatas") or []
    return {m.get("filename") for m in metas if m and m.get("filename")}


def ingest() -> None:
    from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore

    configure_embeddings_only()

    if not PDF_DIR.exists() or not any(PDF_DIR.glob("*.pdf")):
        raise FileNotFoundError(
            f"No PDFs found in {PDF_DIR}. Drop 10-20 FERC/PJM PDFs there and re-run."
        )

    collection = get_chroma_collection()
    already = ingested_filenames(collection)
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    new_pdfs = [p for p in pdfs if p.name not in already]

    print(f"Found {len(pdfs)} PDFs in {PDF_DIR}")
    print(f"  Already ingested: {len(already)}")
    print(f"  New to ingest:    {len(new_pdfs)}")

    if not new_pdfs:
        print("Nothing to do. Vector store is up to date.")
        return

    documents = SimpleDirectoryReader(
        input_files=[str(p) for p in new_pdfs],
        filename_as_id=True,
    ).load_data()

    for doc in documents:
        src = Path(doc.metadata.get("file_path", ""))
        doc.metadata["filename"] = src.name
        doc.metadata["doc_date"] = _guess_date_from_filename(src.name)

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    print(f"\nIngested {len(documents)} document(s) into '{collection.name}'.")
    print(f"Collection now has {collection.count()} chunks.")


def _guess_date_from_filename(name: str) -> str | None:
    import re

    m = re.search(r"(20\d{2})[-_]?(\d{2})?[-_]?(\d{2})?", name)
    if not m:
        return None
    parts = [p for p in m.groups() if p]
    return "-".join(parts)


if __name__ == "__main__":
    ingest()
