# System Design

## Goal

Build a measurable, production-style RAG system that can ingest many file types, answer questions from local files, and keep a useful benchmark trail over time.

## Architecture

The pipeline is organized as a sequence of stages:

1. Ingestion
2. Chunking
3. Retrieval
4. Generation
5. Evaluation
6. Reporting

Each stage has a narrow responsibility so it can be tuned independently.

## Ingestion Layer

The ingestion layer reads many common file types, including:

- TXT
- Markdown
- PDF
- DOCX
- HTML
- CSV
- XLSX
- code-like files such as JSON, YAML, CSS, XML, SQL, JS, and TS

The extractor returns normalized text plus metadata like file path, extension, kind, page count, title, row counts, and sheet counts when available.

## Chunking Layer

Chunking is format-aware:

- Markdown uses section-aware splitting
- CSV and spreadsheet content is split row-wise
- other documents use paragraph splitting and overlapping windows when needed

This keeps chunks small enough to retrieve while preserving the local structure of the source.

## Retrieval Layer

Retrieval is hybrid:

- BM25 handles exact keyword matching
- dense retrieval handles semantic similarity
- reciprocal rank fusion combines both candidate lists

The orchestrator exposes both fused results and raw component traces so debugging is visible.

## Generation Layer

Generation uses the retrieved chunks to produce a grounded answer.

The current setup prefers Groq when a valid `GROQ_API_KEY` is available, with a local fallback for offline or no-key behavior.

The prompt is designed to:

- answer directly
- stay close to evidence
- avoid inventing details
- keep answers concise enough for inspection

## Evaluation Layer

Evaluation tracks:

- context precision
- context recall
- faithfulness
- answer relevancy
- reference similarity in benchmark mode

These scores are heuristic, but they are good enough to compare runs and spot regressions.

## Reporting Layer

Each run can write:

- per-question JSON reports
- benchmark summary JSON and Markdown
- benchmark comparison JSON and Markdown
- benchmark history summaries

This is what makes the pipeline measurable instead of just functional.

## Debugging Workflow

For local debugging, the CLI can print:

- the final answer
- the retrieved context used to answer
- the raw BM25 results
- the raw dense results

That helps identify whether a bad answer is caused by retrieval, chunking, or generation.

## Current Baseline

The latest benchmark run shows the system is working as intended:

- retrieval is returning useful context
- benchmark summaries are generated successfully
- comparison reports work
- the pipeline is now a stable baseline for further tuning

The remaining improvements are mostly retrieval quality and corpus coverage, not basic plumbing.

