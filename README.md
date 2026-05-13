# Interconnection tools

One front door for two dashboards on the U.S. grid interconnection queue:

- **⚡ Operator simulator** — multi-state survival simulation of how today's queue clears over the next decade, with an interactive scenario panel for operator-side policy levers.
- **📚 Document corpus** — RAG pipeline over FERC Order 2023, the rehearing order, and PJM tariff/study filings, with inline citations.

Built as a portfolio piece exploring the data problem Tapestry (Alphabet/X) is solving for grid operators — approached from the public-data layer, with two angles on the same fragmented-data problem.

## Why a combined repo

The two dashboards exist as standalone repos with their own histories:

- [`interconnection-queue-analysis`](https://github.com/keanuhea/interconnection-queue-analysis) — the structured-data simulation, alone
- [`ferc-pjm-rag`](https://github.com/keanuhea/ferc-pjm-rag) — the document corpus, alone

This repo is the integrated experience — one URL, one navigation, the unified narrative. Each dashboard still tells its own story; the cover page stitches them.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Two data dependencies — both gitignored, both manual:

1. **LBNL Queued Up workbook** → `data/LBNL_Ix_Queue_Data_File_thru2025.xlsx`. Download from https://emp.lbl.gov/queues.
2. **Source PDFs for the corpus** → `data/pdfs/*.pdf`. The seed corpus is 5 documents (FERC Order 2023 final rule, Order 2023-A rehearing, PJM interconnection reform progress fact sheet, PJM generation interconnection fact sheet, one sample PJM facility study). See the `ingest.py` source for URLs, or run `cp ../ferc-pjm-rag/data/pdfs/*.pdf data/pdfs/` if you have the companion repo locally.

Build the vector index (free — local embeddings):

```bash
python -m src.corpus.ingest
```

(Optional) Set up an Anthropic API key for AI-generated outputs:

```bash
cp .env.example .env
# add ANTHROPIC_API_KEY=sk-ant-...
```

Without the key: the operator dashboard works fully (the AI brief button shows a friendly fallback); the corpus retrieves and displays chunks but doesn't synthesize answers.

## Run

```bash
streamlit run app.py
```

The cover page opens at http://localhost:8501. From there, navigate to either dashboard.

## Project structure

```
interconnection-tools/
  app.py                       # entry point + page registry
  pages/
    0_Cover.py                 # landing page with narrative + nav CTAs
    1_Operator_view.py         # the structured-data simulation
    2_Document_corpus.py       # the RAG chat dashboard
  src/
    operator/                  # code from interconnection-queue-analysis
      load_data.py
      state_machine.py
      forward_sim.py
      withdrawal_model.py
      concentration_analysis.py
      pjm_queue.py
      pjm_scoring.py
      scenario_brief.py
    corpus/                    # code from ferc-pjm-rag
      config.py
      ingest.py
      query.py
      eval.py
  data/
    LBNL_Ix_Queue_Data_File_thru2025.xlsx   (gitignored)
    pjm_snapshots/                          (committed — small parquets)
    pdfs/                                   (gitignored)
  chroma_db/                                (gitignored)
  eval_set.json                # 10 RAG eval questions
  requirements.txt
  .env.example
```

## Tech stack

| Layer | Tool |
|---|---|
| Structured analytics + simulation | pandas, scikit-learn, numpy |
| Plotting | plotly |
| Dashboard | streamlit (multipage via `st.navigation`) |
| Embeddings | sentence-transformers (BAAI/bge-small-en-v1.5, local) |
| Vector store | ChromaDB (persistent, local) |
| LLM | Claude Sonnet 4.6 via the Anthropic API |
| PDF parsing | pypdf + llama-index-readers-file |

## Data sources

- Berkeley Lab Electricity Markets and Policy Group, *Queued Up: 2025 Edition* — https://emp.lbl.gov/queues
- PJM Interconnection planning API for live queue snapshots — `services.pjm.com/PJMPlanningApi`
- FERC eLibrary (dockets RM22-14, RM22-14-001) for orders 2023 + 2023-A
- PJM publications portal for fact sheets and facility studies
