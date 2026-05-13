"""Run the eval set against the pipeline.

Two modes:
- Default: full RAG (retrieve + Claude generation). Requires ANTHROPIC_API_KEY.
- `--retrieve-only`: print top-k retrieved chunks per question. Free, no API key.

Manual review, not scored — the point is to read answers + citations and form
a judgment about retrieval quality and cross-document reasoning.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.corpus.query import ask, format_citations, retrieve

EVAL_PATH = Path(__file__).resolve().parent.parent.parent / "eval_set.json"


def run_eval(retrieve_only: bool = False) -> None:
    questions = json.loads(EVAL_PATH.read_text())
    has_key = bool(os.getenv("ANTHROPIC_API_KEY"))

    if retrieve_only or not has_key:
        if not has_key and not retrieve_only:
            print("(No ANTHROPIC_API_KEY — running retrieve-only)\n")
        for i, item in enumerate(questions, 1):
            q = item["question"]
            print("=" * 80)
            print(f"[{i}/{len(questions)}] {q}")
            print("=" * 80)
            citations = retrieve(q)
            print(format_citations(citations))
            for j, c in enumerate(citations, 1):
                print(f"\n  --- chunk [{j}] preview ---")
                print(f"  {c.text[:300]}")
            print()
        return

    for i, item in enumerate(questions, 1):
        q = item["question"]
        print("=" * 80)
        print(f"[{i}/{len(questions)}] {q}")
        print("=" * 80)
        result = ask(q)
        print(f"\n{result.answer}\n")
        print("Sources:")
        print(format_citations(result.citations))
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--retrieve-only",
        action="store_true",
        help="Skip Claude generation; just print top-k retrieved chunks per question.",
    )
    args = parser.parse_args()
    run_eval(retrieve_only=args.retrieve_only)
