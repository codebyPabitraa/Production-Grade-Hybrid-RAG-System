from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rag_pipeline.cli import run_cli
from rag_pipeline.evaluation.simple import evaluate_against_reference


def load_questions(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "questions" in data:
        data = data["questions"]
    if not isinstance(data, list):
        raise ValueError("Questions file must contain a list or a {\"questions\": [...]} object")
    questions: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, str):
            questions.append({"question": item})
        elif isinstance(item, dict) and "question" in item:
            questions.append(item)
        else:
            raise ValueError("Each benchmark question must be a string or an object with a 'question' field")
    return questions


def run_benchmark(
    questions_file: Path,
    *,
    input_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    report_dir: Path,
) -> dict[str, Any]:
    questions = load_questions(questions_file)
    report_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for entry in questions:
        question = entry["question"]
        reference_answer = entry.get("reference_answer")
        result = run_cli(
            question=question,
            input_dir=input_dir,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            report_dir=report_dir,
        )
        result["reference_similarity"] = evaluate_against_reference(result.get("answer", ""), reference_answer)
        results.append({"question": question, **result})

    metrics = {
        "question_count": len(results),
        "avg_context_precision": sum(item["context_precision"] for item in results) / len(results) if results else 0.0,
        "avg_answer_relevancy": sum(item["answer_relevancy"] for item in results) / len(results) if results else 0.0,
        "avg_faithfulness": sum(item["faithfulness"] for item in results) / len(results) if results else 0.0,
        "avg_context_recall": sum(item["context_recall"] for item in results) / len(results) if results else 0.0,
        "avg_reference_similarity": sum(item.get("reference_similarity", 0.0) for item in results) / len(results) if results else 0.0,
    }
    summary = {
        "questions_file": str(questions_file),
        "run_count": len(results),
        "metrics": metrics,
        "results": results,
        "answers": [
            {
                "question": item["question"],
                "answer": item.get("answer", ""),
                "report_path": item["report_path"],
            }
            for item in results
        ],
    }
    summary_path = report_dir / "benchmark_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = report_dir / "benchmark_summary.md"
    markdown_path.write_text(_build_markdown_summary(summary), encoding="utf-8")
    summary["summary_path"] = str(summary_path)
    summary["markdown_path"] = str(markdown_path)
    return summary


def _build_markdown_summary(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    results = summary["results"]
    lines = [
        "# Benchmark Summary",
        "",
        f"- Questions file: `{summary['questions_file']}`",
        f"- Run count: `{summary['run_count']}`",
        "",
        "## Aggregate Metrics",
        "",
        f"- Avg context precision: `{metrics['avg_context_precision']:.4f}`",
        f"- Avg answer relevancy: `{metrics['avg_answer_relevancy']:.4f}`",
        f"- Avg faithfulness: `{metrics['avg_faithfulness']:.4f}`",
        f"- Avg context recall: `{metrics['avg_context_recall']:.4f}`",
        f"- Avg reference similarity: `{metrics['avg_reference_similarity']:.4f}`",
        "",
        "## Per Question",
        "",
    ]
    for item in results:
        lines.extend(
            [
                f"### {item['question']}",
                "",
                item.get("answer", "").strip(),
                "",
                f"- Report: `{item['report_path']}`",
                f"- Context precision: `{item['context_precision']:.4f}`",
                f"- Answer relevancy: `{item['answer_relevancy']:.4f}`",
                f"- Faithfulness: `{item['faithfulness']:.4f}`",
                f"- Context recall: `{item['context_recall']:.4f}`",
                f"- Reference similarity: `{item.get('reference_similarity', 0.0):.4f}`",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
