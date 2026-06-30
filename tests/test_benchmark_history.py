from pathlib import Path

from rag_pipeline.benchmark_history import build_history_index


def test_build_history_index_writes_files(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "2026_question.json").write_text(
        '{"question":"q","timestamp_utc":"now","evaluation":{"context_precision":0.5,"answer_relevancy":0.4,"faithfulness":0.3,"context_recall":0.2}}',
        encoding="utf-8",
    )

    result = build_history_index(reports_dir)

    assert result["run_count"] == 1
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()

