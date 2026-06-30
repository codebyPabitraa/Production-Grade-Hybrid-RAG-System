from pathlib import Path

from rag_pipeline.benchmark_history import load_latest_answer


def test_load_latest_answer_returns_report(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "2026_question.json").write_text(
        '{"question":"q","answer":"a","evaluation":{}}',
        encoding="utf-8",
    )

    result = load_latest_answer(reports_dir)

    assert result["question"] == "q"
    assert result["answer"] == "a"

