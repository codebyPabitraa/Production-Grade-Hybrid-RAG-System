from pathlib import Path

from rag_pipeline.benchmark_history import latest_benchmark_history_table


def test_latest_benchmark_history_table_prints_rows(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "2026_question.json").write_text(
        '{"question":"q","timestamp_utc":"now","evaluation":{"context_precision":0.5,"answer_relevancy":0.4,"faithfulness":0.3,"context_recall":0.2}}',
        encoding="utf-8",
    )

    table = latest_benchmark_history_table(reports_dir, limit=10)

    assert "Question" in table
    assert "q" in table

