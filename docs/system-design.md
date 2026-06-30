# System Design

## Purpose

This document tracks the architecture and implementation plan for the Production RAG Pipeline + Evaluation Layer.

## Project Structure

- `src/rag_pipeline/ingestion`
- `src/rag_pipeline/chunking`
- `src/rag_pipeline/retrieval`
- `src/rag_pipeline/ranking`
- `src/rag_pipeline/generation`
- `src/rag_pipeline/evaluation`
- `configs`
- `data/raw`
- `data/processed`
- `data/index`
- `scripts`
- `tests`

## Architecture Overview

1. Ingestion
   - load source documents
   - extract text and metadata

2. Chunking
   - split documents into retrieval-friendly segments
   - preserve semantic boundaries where possible

3. Retrieval
   - dense retriever for semantic similarity
   - sparse retriever for lexical matching

4. Fusion
   - combine dense and sparse candidates with RRF

5. Reranking
   - use a cross-encoder to rank the merged candidates

6. Generation
   - send top-ranked context to the LLM
   - generate an answer grounded in retrieved sources

7. Evaluation
   - run RAGAS metrics
   - compare baseline and improved pipeline

## Immediate Next Implementation Tasks

1. Add Python project metadata
2. Define configuration files
3. Create module entry points
4. Implement baseline ingestion and chunking
5. Add retrieval and evaluation scaffolding

