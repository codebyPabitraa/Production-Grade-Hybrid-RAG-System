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


def _preview_text(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def format_retrieval_trace(results: list, preview_chars: int = 180) -> str:
    lines = ["Retrieved context:"]
    if not results:
        lines.append("No retrieval results.")
        return "\n".join(lines)

    for result in results:
        source_path = result.chunk.metadata.get("path", result.chunk.doc_id)
        strategy = result.metadata.get("strategy", "unknown")
        lines.append(
            (
                f"[{result.rank}] score={result.score:.4f} strategy={strategy} "
                f"source={source_path} chunk={result.chunk.chunk_id} span={result.chunk.start}:{result.chunk.end}"
            )
        )
        lines.append(_preview_text(result.chunk.text, limit=preview_chars))
    return "\n".join(lines)


def format_component_trace(name: str, results: list, preview_chars: int = 180) -> str:
    lines = [f"{name.upper()} results:"]
    if not results:
        lines.append("No results.")
        return "\n".join(lines)

    for result in results:
        source_path = result.chunk.metadata.get("path", result.chunk.doc_id)
        lines.append(f"[{result.rank}] score={result.score:.4f} source={source_path} chunk={result.chunk.chunk_id}")
        lines.append(_preview_text(result.chunk.text, limit=preview_chars))
    return "\n".join(lines)


def format_why_answer_trace(question: str, results: list, answer_metadata: dict[str, object] | None = None) -> str:
    if answer_metadata and answer_metadata.get("strategy") == "definition_override":
        return "This answer came from a built-in definition override because the question matched a common definition pattern."
    if not results:
        return "No retrieved context was available, so the answer could not be grounded in source files."
    first = results[0]
    source_path = first.chunk.metadata.get("path", first.chunk.doc_id)
    return (
        f"The answer was grounded primarily in the top retrieved chunk from {source_path}. "
        f"That chunk scored {first.score:.4f} for the question '{question}'. "
        "The answer also synthesized the next best chunks when they added supporting detail."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the RAG pipeline over local files.")
    parser.add_argument("--question", required=True, help="Question to ask against the document set.")
    parser.add_argument("--input-dir", default="data/raw", help="Directory containing source documents.")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size for document splitting.")
    parser.add_argument("--chunk-overlap", type=int, default=120, help="Chunk overlap for document splitting.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks to use.")
    parser.add_argument("--report-dir", default="reports", help="Directory for saved evaluation reports.")
    parser.add_argument("--show-context", action="store_true", help="Print retrieved chunks used to answer the question.")
    parser.add_argument("--show-retrieval-components", action="store_true", help="Print raw BM25 and dense retrieval results.")
    return parser


def run_cli(
    question: str,
    input_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    report_dir: Path,
) -> dict[str, object]:
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
    component_results = retriever.search_components(RetrievalQuery(query=question, top_k=top_k))
    sample_results = retriever.search(RetrievalQuery(query=question, top_k=top_k))
    logger.info("Retrieved %s chunks", len(sample_results))

    generated = generate_answer(question, sample_results)
    evaluation = evaluate_answer(question, generated, sample_results)
    why_answer = format_why_answer_trace(question, sample_results, generated.metadata)

    report = build_evaluation_report(
        question,
        generated,
        evaluation,
        documents=len(ingestion_result.documents),
        chunks=len(chunks),
        retrieval_results=len(sample_results),
    )
    report_path = save_evaluation_report(report, output_dir=report_dir)
    citations = []
    for source in generated.sources[:3]:
        citations.append(
            {
                "source_path": str(source.chunk.metadata.get("path", source.chunk.doc_id)),
                "chunk_id": source.chunk.chunk_id,
                "rank": source.rank,
                "score": source.score,
                "preview": source.chunk.text.strip()[:220],
            }
        )

    return {
        "question": question,
        "answer": generated.answer,
        "answer_strategy": generated.metadata.get("strategy", "unknown"),
        "documents": len(ingestion_result.documents),
        "chunks": len(chunks),
        "retrieval_results": len(sample_results),
        "answer_length": len(generated.answer),
        "context_precision": evaluation.context_precision,
        "answer_relevancy": evaluation.answer_relevancy,
        "faithfulness": evaluation.faithfulness,
        "context_recall": evaluation.context_recall,
        "report_path": str(report_path),
        "retrieved_context": format_retrieval_trace(sample_results),
        "bm25_context": format_component_trace("bm25", component_results["bm25"]),
        "dense_context": format_component_trace("dense", component_results["dense"]),
        "why_answer": why_answer,
        "citations": citations,
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
    if args.show_context:
        print(result["retrieved_context"])
    if args.show_retrieval_components:
        print(result["bm25_context"])
        print(result["dense_context"])
    print({key: value for key, value in result.items() if key not in {"answer", "retrieved_context", "bm25_context", "dense_context"}})
    return 0
