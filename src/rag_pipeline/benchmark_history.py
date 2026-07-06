from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rag_pipeline.storage import reports_root


def load_benchmark_runs(reports_dir: Path = reports_root()) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("*_*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        if path.name in {"benchmark_comparison.json"}:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or "question" not in data:
            continue
        evaluation = data.get("evaluation", {})
        run = {
            "report_path": str(path),
            "question": data.get("question"),
            "timestamp_utc": data.get("timestamp_utc"),
            "summary": data.get("summary", {}),
            "metrics": {
                "context_precision": evaluation.get("context_precision", 0.0),
                "answer_relevancy": evaluation.get("answer_relevancy", 0.0),
                "faithfulness": evaluation.get("faithfulness", 0.0),
                "context_recall": evaluation.get("context_recall", 0.0),
            },
        }
        runs.append(run)
    return runs


def build_history_index(reports_dir: Path = reports_root(), output_path: Path | None = None) -> dict[str, Any]:
    runs = load_benchmark_runs(reports_dir)
    index = {
        "reports_dir": str(reports_dir),
        "run_count": len(runs),
        "runs": runs,
    }
    output_path = output_path or (reports_dir / "benchmark_history.json")
    output_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(_build_markdown(index), encoding="utf-8")
    index["json_path"] = str(output_path)
    index["markdown_path"] = str(markdown_path)
    return index


def build_history_table(index: dict[str, Any], limit: int = 10) -> str:
    runs = index.get("runs", [])[:limit]
    headers = ["Question", "Context P", "Answer R", "Faith", "Recall"]
    rows = []
    for run in runs:
        metrics = run["metrics"]
        rows.append(
            [
                str(run["question"])[:42],
                f"{metrics['context_precision']:.3f}",
                f"{metrics['answer_relevancy']:.3f}",
                f"{metrics['faithfulness']:.3f}",
                f"{metrics['context_recall']:.3f}",
            ]
        )
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    lines = []
    lines.append(" | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    lines.append("-+-".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        lines.append(" | ".join(row[i].ljust(widths[i]) for i in range(len(headers))))
    return "\n".join(lines)


def _build_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# Benchmark History",
        "",
        f"- Reports dir: `{index['reports_dir']}`",
        f"- Run count: `{index['run_count']}`",
        "",
    ]
    for run in index["runs"][:20]:
        metrics = run["metrics"]
        lines.extend(
            [
                f"## {run['question']}",
                f"- Report: `{run['report_path']}`",
                f"- Timestamp: `{run.get('timestamp_utc', 'unknown')}`",
                f"- Context precision: `{metrics['context_precision']:.4f}`",
                f"- Answer relevancy: `{metrics['answer_relevancy']:.4f}`",
                f"- Faithfulness: `{metrics['faithfulness']:.4f}`",
                f"- Context recall: `{metrics['context_recall']:.4f}`",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def load_latest_answer(reports_dir: Path = reports_root()) -> dict[str, Any]:
    latest_report = None
    for path in sorted(reports_dir.glob("*_*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        if path.name in {"benchmark_comparison.json"}:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "answer" in data and "question" in data:
            latest_report = {"report_path": str(path), **data}
            break
    if latest_report is None:
        raise FileNotFoundError(f"No saved answer report found in {reports_dir}")
    return latest_report


def load_latest_answers(reports_dir: Path = reports_root(), limit: int = 5) -> list[dict[str, Any]]:
    latest_answers: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("*_*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        if path.name in {"benchmark_comparison.json"}:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "answer" in data and "question" in data:
            latest_answers.append({"report_path": str(path), **data})
        if len(latest_answers) >= limit:
            break
    return latest_answers


def latest_benchmark_history_table(reports_dir: Path = reports_root(), limit: int = 10) -> str:
    index = build_history_index(reports_dir)
    return build_history_table(index, limit=limit)
