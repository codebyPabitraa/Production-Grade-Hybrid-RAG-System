from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_pipeline.evaluation.types import EvaluationResult
from rag_pipeline.generation.types import GeneratedAnswer
from rag_pipeline.storage import reports_root


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value).strip("_")


def build_evaluation_report(
    question: str,
    generated: GeneratedAnswer,
    evaluation: EvaluationResult,
    *,
    documents: int,
    chunks: int,
    retrieval_results: int,
    reference_answer: str | None = None,
) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "reference_answer": reference_answer,
        "answer": generated.answer,
        "generated": asdict(generated),
        "evaluation": asdict(evaluation),
        "summary": {
            "documents": documents,
            "chunks": chunks,
            "retrieval_results": retrieval_results,
        },
    }


def save_evaluation_report(report: dict[str, Any], output_dir: Path = reports_root()) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    question = report.get("question", "report")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{timestamp}_{_safe_name(question)[:40]}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
