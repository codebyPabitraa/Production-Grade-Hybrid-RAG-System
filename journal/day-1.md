# Day 1

## Primary Goal

Build a production-style RAG pipeline that could eventually:

- accept many file formats
- extract usable content
- chunk the content intelligently
- retrieve relevant passages
- rank them well
- support evaluation and measurable improvement

At the start, the project was framed as a RAG system with an evaluation layer. The main idea was to prove that retrieval quality could improve in a measurable way, not just to build a simple chat demo.

## Initial Scope

The first idea was narrower:

- create a basic RAG pipeline
- use text files first
- build a baseline ingestion and chunking flow
- add a README or design file to capture the architecture

That scope was enough to get moving, but it did not fully match the real project goal.

## Why The Scope Changed

As we continued, it became clear that the pipeline needed to be broader than text-only ingestion.

The real requirement was:

- the system must accept many kinds of uploaded files
- the ingestion layer must normalize them
- the rest of the pipeline must work on that normalized representation

That meant the project had to move from:

- “text RAG demo”

to:

- “universal document ingestion + RAG pipeline”

This was an important correction, because the value of the project depends on handling real-world file types, not just plain text.

## Problems We Faced

### 1. No Existing Project Structure

At the beginning, the workspace was basically empty.

There was no existing codebase to extend, so we had to create:

- package layout
- docs
- configs
- scripts
- tests
- data folders

### 2. No Reliable Python Path At First

We ran into a Windows environment problem early.

The initial `.venv` was created from a Python interpreter path that later turned out to be unreliable from some shells.

Symptoms included:

- `python` not found in the shell
- `pytest` not found in the shell
- venv launchers pointing at a Python path that could not be executed
- `ImportError` from a partially broken `pip`
- editable install not completing cleanly

### 3. Corrupted Virtual Environment State

While fixing the environment, `pip` was briefly left in a broken state inside `.venv`.

That caused:

- install failures
- import failures for the package
- missing module errors during tests

The root issue was not the code itself. It was the environment.

### 4. The Test Expectations Changed As The Design Changed

Once ingestion became universal and retrieval became richer, some early tests became outdated.

Examples:

- tests expecting only `.txt` and `.md`
- tests expecting the router to return a raw string instead of structured extracted content

Those tests had to be updated to reflect the new architecture.

## How We Fixed The Environment

We rebuilt the venv from the known working Python 3.12 executable:

- recreated `.venv`
- activated it in PowerShell
- upgraded `pip`, `setuptools`, and `wheel`
- reinstalled the project in editable mode
- installed dev dependencies
- reran the baseline and test suite

This restored a healthy development loop.

## What We Primarily Did First

### 1. Defined The Project

We wrote:

- `README.md`
- `docs/system-design.md`

These established:

- the project goal
- the architecture
- the implementation phases
- the metrics we wanted to track

### 2. Created The Project Skeleton

We added the initial directory structure:

- `src/`
- `configs/`
- `data/`
- `scripts/`
- `tests/`
- `notebooks/`

This gave the project a place to grow in a controlled way.

### 3. Added Python Packaging

We introduced:

- `pyproject.toml`
- `requirements.txt`

This made the project installable and testable as a package.

### 4. Built The Baseline Pipeline

The first version of the pipeline included:

- ingestion
- chunking
- a runnable baseline script

This was intentionally minimal so we could verify the end-to-end flow early.

### 5. Added Config And Logging

We added:

- YAML config loading
- structured logging

That made the pipeline easier to run and easier to debug.

## Changes We Made Afterwards

### 1. Expanded Ingestion

The ingestion layer was changed from text-only to format-aware universal ingestion.

We added extractors for:

- TXT
- MD
- PDF
- DOCX
- HTML
- CSV
- XLSX
- code and text-like files such as JSON, YAML, CSS, XML, SQL, JS, and TS

We also introduced a shared extraction schema so each file type could return:

- normalized text
- metadata

This was a key architectural step.

### 2. Added File-Type Metadata

The normalized document metadata began carrying useful hints such as:

- file path
- extension
- document kind
- page count
- paragraph count
- title
- row counts
- sheet counts
- language hints for code

That metadata later helps chunking and retrieval behave more intelligently.

### 3. Made Chunking Format-Aware

Chunking moved from simple sliding windows to a more structured strategy:

- markdown uses heading-aware sections
- CSV and spreadsheets are treated as row-oriented content
- all other files use paragraph-aware splitting
- long sections still fall back to overlapping windows

This was necessary because different file types need different segmentation logic.

### 4. Built The Retrieval Foundation

We added a retrieval abstraction and then grew it into a retrieval stack:

- `Retriever` interface
- `RetrievalQuery`
- `RetrievalResult`
- keyword retriever prototype
- BM25 retriever
- dense vector-style retriever
- reciprocal rank fusion

This gave us a real retrieval layer instead of a placeholder.

### 5. Wired Retrieval Into The Baseline

The baseline pipeline was updated to:

- ingest documents
- chunk them
- create a retriever
- run a sample retrieval query
- log retrieval output

That confirmed the pipeline could move from input to retrieval end to end.

### 6. Added Tests Throughout

We added tests for:

- chunking
- chunking strategies
- ingestion
- ingestion router
- keyword retrieval
- BM25 retrieval
- dense retrieval
- fusion

This gave us confidence that changes were not breaking the foundation.

### 7. Added Generation, Evaluation, Reporting, And CLI Support

We then expanded the project beyond retrieval into the answer pipeline:

- structured prompt building for generation
- a local answer fallback for offline behavior
- hosted provider support for OpenAI and then Groq
- `.env` loading so secrets stay local
- JSON evaluation reports for each run
- a CLI entry point for asking custom questions

This made the project usable end to end instead of only being a retrieval demo.

## Important Design Correction

One major correction happened during the day:

At first, the pipeline was treated like a text/document pipeline.

Later we corrected that to:

- a universal file ingestion pipeline
- followed by normalization
- followed by chunking
- followed by retrieval
- followed by generation and evaluation

That correction changed the shape of the work significantly.

## What We Learned

- Real RAG systems need stronger ingestion than a simple text loader.
- File-type handling is part of the architecture, not an afterthought.
- Metadata matters because it improves later stages of the pipeline.
- Tests must evolve as the design evolves.
- Environment stability is essential on Windows when working with Python venvs.
- It is better to fix the model of the system early than to keep building the wrong abstraction.
- Secret handling matters. We had to move API keys into `.env` and ensure `.gitignore` kept them out of version control.
- Hosted LLM integrations can fail for simple reasons like the wrong model name or a placeholder API key, so provider selection needs guardrails.
- Groq became the preferred hosted path after the OpenAI placeholder key caused a 401 and Groq returned a successful 200 once the model was corrected.

## Final State At End Of Day

By the end of the day, the project had:

- a working package structure
- a written design document
- a baseline pipeline
- universal ingestion
- format-aware chunking
- BM25, dense retrieval, and RRF fusion
- a passing test suite

## End-Of-Day Status

The project ended in a healthy state.

The core foundation is now ready for the next phase:

- retrieval orchestrator API
- answer generation
- evaluation and metrics logging
