from pathlib import Path

from rag_pipeline.benchmark_compare import compare_benchmarks


def test_compare_benchmarks_writes_outputs(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text('{"metrics":{"avg_context_precision":0.1}}', encoding="utf-8")
    candidate.write_text('{"metrics":{"avg_context_precision":0.2}}', encoding="utf-8")

    result = compare_benchmarks(baseline, candidate, output_dir=tmp_path / "reports")

    assert result["deltas"]["avg_context_precision"] == 0.1
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()

