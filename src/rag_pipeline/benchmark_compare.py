from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def resolve_summary_path(path: Path) -> Path:
    if path.is_file():
        return path
    if path.is_dir():
        candidates = sorted(path.rglob("benchmark_summary.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0]
    raise FileNotFoundError(
        f"Could not find a benchmark_summary.json at {path}. "
        "Pass a summary file path or a directory containing one."
    )


def load_summary(path: Path) -> dict[str, Any]:
    resolved = resolve_summary_path(path)
    return json.loads(resolved.read_text(encoding="utf-8"))


def compare_benchmarks(baseline_path: Path, candidate_path: Path, output_dir: Path = Path("reports")) -> dict[str, Any]:
    baseline_resolved = resolve_summary_path(baseline_path)
    candidate_resolved = resolve_summary_path(candidate_path)
    baseline = load_summary(baseline_resolved)
    candidate = load_summary(candidate_resolved)

    baseline_metrics = baseline.get("metrics", {})
    candidate_metrics = candidate.get("metrics", {})

    def delta(metric: str) -> float:
        return float(candidate_metrics.get(metric, 0.0)) - float(baseline_metrics.get(metric, 0.0))

    comparison = {
        "baseline": str(baseline_resolved),
        "candidate": str(candidate_resolved),
        "deltas": {
            "avg_context_precision": delta("avg_context_precision"),
            "avg_answer_relevancy": delta("avg_answer_relevancy"),
            "avg_faithfulness": delta("avg_faithfulness"),
            "avg_context_recall": delta("avg_context_recall"),
            "avg_reference_similarity": delta("avg_reference_similarity"),
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "benchmark_comparison.json"
    md_path = output_dir / "benchmark_comparison.md"
    json_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_build_markdown(comparison), encoding="utf-8")
    comparison["json_path"] = str(json_path)
    comparison["markdown_path"] = str(md_path)
    return comparison


def _build_markdown(comparison: dict[str, Any]) -> str:
    deltas = comparison["deltas"]
    lines = [
        "# Benchmark Comparison",
        "",
        f"- Baseline: `{comparison['baseline']}`",
        f"- Candidate: `{comparison['candidate']}`",
        "",
        "## Metric Deltas",
        "",
    ]
    for key, value in deltas.items():
        lines.append(f"- {key}: `{value:+.4f}`")
    return "\n".join(lines) + "\n"


def snapshot_latest_summary(source: Path, destination_dir: Path) -> Path:
    resolved = resolve_summary_path(source)
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / "benchmark_summary.json"
    shutil.copy2(resolved, target)
    return target
