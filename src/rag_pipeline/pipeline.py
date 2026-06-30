from __future__ import annotations

import logging

from rag_pipeline.chunking import chunk_documents
from rag_pipeline.config import PipelineConfig
from rag_pipeline.evaluation import build_evaluation_report, evaluate_answer, save_evaluation_report
from rag_pipeline.generation import generate_answer
from rag_pipeline.ingestion import ingest_text_files
from rag_pipeline.retrieval import RetrievalOrchestrator, RetrievalQuery

logger = logging.getLogger(__name__)


def run_baseline_pipeline(config: PipelineConfig) -> dict[str, int]:
    logger.info("Starting baseline pipeline")
    ingestion_result = ingest_text_files(config.ingestion.input_dir)
    logger.info("Loaded %s documents from %s", len(ingestion_result.documents), ingestion_result.source_dir)
    chunks = chunk_documents(
        ingestion_result.documents,
        chunk_size=config.chunking.chunk_size,
        chunk_overlap=config.chunking.chunk_overlap,
    )
    logger.info("Created %s chunks", len(chunks))

    retriever = RetrievalOrchestrator(chunks)
    sample_results = retriever.search(RetrievalQuery(query="production rag pipeline", top_k=3))
    logger.info("Sample retrieval produced %s results", len(sample_results))

    generated = generate_answer("What is this project about?", sample_results)
    logger.info("Generated answer length: %s", len(generated.answer))

    evaluation = evaluate_answer("What is this project about?", generated, sample_results)
    logger.info(
        "Evaluation scores | context_precision=%.3f | answer_relevancy=%.3f | faithfulness=%.3f | context_recall=%.3f",
        evaluation.context_precision,
        evaluation.answer_relevancy,
        evaluation.faithfulness,
        evaluation.context_recall,
    )
    report = build_evaluation_report(
        "What is this project about?",
        generated,
        evaluation,
        documents=len(ingestion_result.documents),
        chunks=len(chunks),
        retrieval_results=len(sample_results),
    )
    report_path = save_evaluation_report(report)
    logger.info("Saved evaluation report to %s", report_path)

    return {
        "documents": len(ingestion_result.documents),
        "chunks": len(chunks),
        "retrieval_results": len(sample_results),
        "answer_length": len(generated.answer),
        "context_precision": int(evaluation.context_precision * 1000),
    }
