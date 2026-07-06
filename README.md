# RAG Pipeline

Production-style retrieval augmented generation pipeline for local files.

## What This Project Does

The pipeline ingests many file types, normalizes the content, chunks it in a format-aware way, retrieves relevant context with hybrid search, generates grounded answers, evaluates the result, and saves reports for later comparison.

It is designed to be measurable, benchmarkable, and easy to inspect while staying free to run with a local corpus and an optional Groq API key.

## Current Milestone

The project now has:

- universal file ingestion
- format-aware chunking
- BM25 + dense retrieval with RRF fusion
- Groq-backed generation with local fallback
- evaluation metrics and saved reports
- benchmark summaries and comparison reports
- CLI debugging for retrieved context and retrieval components

## Quick Start

```powershell
cd C:\RAG_PIPELINE
.\.venv\Scripts\Activate.ps1
python -m pytest
python .\scripts\run_cli.py --question "What is this project about?" --show-context --show-retrieval-components
python .\scripts\run_benchmark.py --questions-file .\data\benchmark_questions_with_references.json
```

## Environment

Create a local `.env` file if you want hosted generation:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

The project keeps `.env` out of version control.

## Key Scripts

- `scripts/run_cli.py` runs one question against the local corpus.
- `scripts/run_benchmark.py` runs the benchmark question set and saves a summary.
- `scripts/compare_benchmarks.py` compares baseline and candidate benchmark summaries.
- `scripts/show_latest_answer.py` prints the latest saved answer.
- `scripts/show_benchmark_history.py` shows a compact benchmark history table.
- `scripts/generate_dashboard.py` writes a static benchmark dashboard HTML file.
- `scripts/open_dashboard.ps1` generates the dashboard and opens it in your browser.
- `scripts/run_app.py` starts the local upload-and-ask demo server.

The upload demo lets you post files, ask a question, and inspect the answer with evaluation metrics in a single local page.
Uploaded files first land in a pending queue. Use the admin page to approve them into permanent storage before they are included in question answering.
The admin queue also supports review notes, and the app shows the approved corpus so you can see what is live.
The public UI explains the RAG metrics up front and hides raw retrieval traces so it reads like a product page instead of a debugging console.
The local demo now includes basic JWT-style login, email OTP verification, and environment-based admin bootstrapping for deployment experiments.

## Benchmark State

The current benchmark workflow uses:

- `data/benchmark_questions_with_references.json`
- saved JSON reports in `reports/`
- benchmark summary Markdown and JSON files
- comparison reports for before/after analysis

The benchmark is currently strong enough to act as a stable baseline while we keep tuning retrieval quality.

## Journal

Development notes are tracked in:

- `journal/day-1.md`
- `journal/day-2.md`
- `journal/day-3.md`

Those entries record the project goal, the problems we hit, and why the architecture changed over time.
