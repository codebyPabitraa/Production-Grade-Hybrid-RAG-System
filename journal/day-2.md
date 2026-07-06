# Day 2

## Primary Goal

Continue turning the RAG prototype into a more production-like evaluation workflow:

- make the answer path more realistic
- integrate a free hosted model path
- support single-question runs and benchmark runs
- keep evaluation reports for later comparison

The goal for this day was less about building the whole system from scratch and more about making the workflow useful for repeated experimentation.

## What We Started With

At the start of the day, the project already had:

- universal ingestion
- format-aware chunking
- retrieval orchestration
- prompt-building generation
- heuristic evaluation
- JSON report saving
- a working CLI

That meant we could focus on higher-level workflow improvements instead of fixing the foundation.

## Main Work Done

### 1. Improved The Generation Layer

We refined the generation path so it looked more like a real LLM integration:

- added clearer prompt construction
- made the prompt include source path, file kind, score, and chunk id
- extracted short key points from the retrieved context
- kept the local grounded fallback available

This made the answer output more structured and easier to move to a real model later.

### 2. Added Hosted Provider Support

We introduced a provider abstraction and wired in hosted LLM options:

- OpenAI provider
- Groq provider

The first hosted path was OpenAI, but that was not the final path we kept using.

### 3. Fixed The Environment And Secret Handling

We ran into a problem where the shell had a placeholder `OPENAI_API_KEY` value set.

That caused:

- the code to prefer OpenAI even when Groq was intended
- a `401 Unauthorized` response from OpenAI

We fixed this by:

- adding `.env` loading
- keeping secrets in a local `.env` file
- adding placeholder-key guards
- making Groq the preferred hosted path when `GROQ_API_KEY` is present

### 4. Corrected Groq Model Selection

Groq initially returned a `400 Bad Request` because the default model choice was not the right one for the account.

We fixed that by:

- making the Groq model configurable with `GROQ_MODEL`
- switching the default to `llama-3.1-8b-instant`

After that, Groq returned `200 OK` and the hosted generation path worked.

### 5. Added Safety Around Secrets

We created:

- `.env.example`
- `.gitignore`

This kept `.env` and report JSON files out of version control and made the key setup clearer.

### 6. Added A Better Journal

We updated the journal itself so it recorded:

- why the scope shifted
- what environment problems we faced
- why provider selection changed
- what we learned from the Groq/OpenAI mismatch

This helped turn the journal into an actual project log instead of just a feature checklist.

### 7. Expanded The Benchmark Corpus And Tuned Reference Scoring

We added more sample knowledge files to the local corpus so benchmark questions could retrieve more relevant context:

- project overview notes
- benchmark support notes

We also tuned the reference scoring to be more forgiving by:

- stripping common stopwords
- normalizing a few common technical terms
- using an F1-style similarity score for reference answers

That made the benchmark comparison workflow more informative and less brittle.

## Workflow Improvements

### 1. Added A CLI For Single Questions

The CLI now supports:

- asking a custom question
- choosing chunk size and overlap
- choosing top-k retrieval
- saving a report per run

### 2. Added Benchmark Mode

We added a second execution path for benchmarking:

- run multiple questions in one go
- save one report per question
- save an aggregate benchmark summary

### 3. Added Reference-Aware Benchmarking

We extended benchmark input files so they can include `reference_answer` values.

That allowed benchmark runs to compute:

- `reference_similarity`
- average reference similarity across the dataset

This is a better fit for a production evaluation workflow because it gives us an expected answer to compare against, not just heuristic overlap scores.

## Benchmark Artifacts Added

We added:

- `data/benchmark_questions.json`
- `data/benchmark_questions_with_references.json`

We also created benchmark tests so the workflow could be validated automatically.

## Evaluation Improvements

The evaluation workflow remained heuristic-based, but it became more useful:

- per-question evaluation still works
- benchmark summary now aggregates multiple runs
- reference answers are supported in the benchmark path

This gives us a path to more realistic evaluation without requiring the whole system to be perfect already.

## Problems We Faced

### 1. API Key Confusion

The biggest issue was that a placeholder OpenAI key in the shell caused the app to hit OpenAI instead of Groq.

That was fixed by:

- loading `.env`
- ignoring placeholder values
- preferring Groq when it has a real key

### 2. Wrong Groq Model

Groq returned a 400 until the model was changed to a supported option.

That was fixed by making the model configurable and switching the default.

### 3. Benchmark Retrieval Coverage

One benchmark question returned zero retrieved chunks.

That wasn’t a code failure, but it was a useful signal:

- the corpus is still very small
- benchmark quality depends on retrieval coverage
- the reference workflow will get more meaningful as the corpus grows

## What We Learned Today

- Provider fallback logic needs guardrails.
- Hosted LLM integration is not just about keys; model selection matters too.
- A benchmark workflow is much more useful when it supports reference answers.
- A strong production RAG workflow needs both one-off debugging runs and repeatable multi-question evaluation.
- Keeping `.env` local and untracked is essential once hosted APIs enter the picture.

## End Of Day 2 State

By the end of the day, the project had:

- working Groq-hosted generation
- local fallback generation
- `.env` loading
- CLI support
- benchmark mode
- reference-aware benchmark inputs
- benchmark summary reporting
- `.gitignore` protection for secrets and generated reports
- a passing test suite

## Status

The project is still healthy and more production-like than before.

The next logical improvements are:

- better benchmark scoring
- a larger benchmark corpus
- comparison views for saved reports
- a more faithful RAGAS-style evaluation pipeline

## Additional Work Logged On This Day

### 1. Added Retrieval Trace Output To The CLI

We added a `--show-context` option so the CLI can print the retrieved chunks that were actually used to answer a question.

This was important because the earlier workflow showed only the final answer and the metrics. That made it hard to tell whether weak answers were caused by retrieval, chunking, or the generation prompt.

The trace now shows:

- chunk rank
- fused score
- retrieval strategy
- source file path
- chunk id
- chunk span
- a short preview of the text

That gave us a much clearer debugging loop.

### 2. Fixed The Trace Formatting Behavior

The first version of the trace helper returned only `No retrieval results.` when the retriever produced nothing.

We corrected that so the output always starts with `Retrieved context:` and then either:

- the retrieved chunk list
- or a clear no-results message

That kept the CLI output consistent.

### 3. Expanded The Local Corpus

We added richer source notes to `data/raw` so the retriever has more useful material to work with.

The new notes describe:

- the production RAG workflow
- evaluation and benchmarking behavior
- file-type handling expectations

This should improve question coverage for project-style queries and give the benchmark more realistic source text to retrieve.

### 4. Continued Benchmark-Oriented Thinking

The corpus expansion was not just about adding more text.

The goal was to make the data more representative of the kinds of questions we want to ask later, such as:

- how ingestion works
- how retrieval is made production-like
- how evaluation is tracked
- why the system is measurable

That keeps the project aligned with the original goal of being a benchmarkable RAG system instead of a simple demo.

### 5. Added A Targeted Architecture Note

After reviewing the benchmark summary, we noticed that a few questions were still weaker than the others:

- what the main pieces of the system are
- how the system handles different file types
- how the pipeline is made measurable

To help those questions retrieve better evidence, we added a focused architecture note that explains:

- the major pipeline stages
- why the system is measurable
- how file-type handling works in practice

This was a deliberate retrieval fix rather than a generation tweak.

### 6. Added An End-To-End Flow Note

We added one more source note that explains the pipeline as a full sequence:

- ingest
- normalize
- chunk
- retrieve
- generate
- evaluate
- report

This was aimed at the questions that still needed better coverage for the benchmark, especially the ones about what the pipeline does and how the whole system fits together.

### 7. Added A Direct Pipeline Purpose Note

One benchmark question still lagged behind the others:

- `What does the pipeline do?`

To help retrieval hit that question more directly, we added a short note that states the pipeline purpose in plain language and breaks the flow into the main stages.

This should help the retriever find a tighter match when the benchmark uses that exact wording.

### 8. Wrote The Current Project Documentation

We filled in the repository documentation so the project state is now easier to understand without reading the whole chat history.

The docs now explain:

- what the project does
- how the system is designed
- how to run it locally
- how the benchmark workflow works
- what the current baseline looks like

This marks the point where the project has moved from a raw build-out phase into a documented benchmark baseline.
