from __future__ import annotations

import argparse
import logging
from pathlib import Path

from rag_pipeline.chunking import chunk_documents
from rag_pipeline.config import PipelineConfig
from rag_pipeline.evaluation import build_evaluation_report, evaluate_answer, save_evaluation_report
from rag_pipeline.generation import generate_answer
from rag_pipeline.ingestion import ingest_text_files
from rag_pipeline.env import load_dotenv
from rag_pipeline.retrieval import RetrievalOrchestrator, RetrievalQuery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the RAG pipeline over local files.")
    parser.add_argument("--question", required=True, help="Question to ask against the document set.")
    parser.add_argument("--input-dir", default="data/raw", help="Directory containing source documents.")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size for document splitting.")
    parser.add_argument("--chunk-overlap", type=int, default=120, help="Chunk overlap for document splitting.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks to use.")
    parser.add_argument("--report-dir", default="reports", help="Directory for saved evaluation reports.")
    return parser


def run_cli(question: str, input_dir: Path, chunk_size: int, chunk_overlap: int, top_k: int, report_dir: Path) -> dict[str, str | int | float]:
    logger = logging.getLogger(__name__)
    config = PipelineConfig()
    config.ingestion.input_dir = input_dir
    config.chunking.chunk_size = chunk_size
    config.chunking.chunk_overlap = chunk_overlap

    ingestion_result = ingest_text_files(config.ingestion.input_dir)
    logger.info("Loaded %s documents from %s", len(ingestion_result.documents), ingestion_result.source_dir)

    chunks = chunk_documents(ingestion_result.documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info("Created %s chunks", len(chunks))

    retriever = RetrievalOrchestrator(chunks)
    sample_results = retriever.search(RetrievalQuery(query=question, top_k=top_k))
    logger.info("Retrieved %s chunks", len(sample_results))

    generated = generate_answer(question, sample_results)
    evaluation = evaluate_answer(question, generated, sample_results)

    report = build_evaluation_report(
        question,
        generated,
        evaluation,
        documents=len(ingestion_result.documents),
        chunks=len(chunks),
        retrieval_results=len(sample_results),
    )
    report_path = save_evaluation_report(report, output_dir=report_dir)

    return {
        "question": question,
        "answer": generated.answer,
        "documents": len(ingestion_result.documents),
        "chunks": len(chunks),
        "retrieval_results": len(sample_results),
        "answer_length": len(generated.answer),
        "context_precision": evaluation.context_precision,
        "answer_relevancy": evaluation.answer_relevancy,
        "faithfulness": evaluation.faithfulness,
        "context_recall": evaluation.context_recall,
        "report_path": str(report_path),
    }


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    result = run_cli(
        question=args.question,
        input_dir=Path(args.input_dir),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        top_k=args.top_k,
        report_dir=Path(args.report_dir),
    )

    print(result["answer"])
    print({key: value for key, value in result.items() if key != "answer"})
    return 0
