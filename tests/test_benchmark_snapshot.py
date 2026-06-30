from pathlib import Path

from rag_pipeline.benchmark_compare import snapshot_latest_summary


def test_snapshot_latest_summary_copies_file(tmp_path: Path):
    source_dir = tmp_path / "reports"
    source_dir.mkdir()
    summary = source_dir / "benchmark_summary.json"
    summary.write_text('{"metrics": {}}', encoding="utf-8")

    target = snapshot_latest_summary(source_dir, tmp_path / "baseline")

    assert target.exists()
    assert target.name == "benchmark_summary.json"

