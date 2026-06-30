from pathlib import Path

from rag_pipeline.benchmark_history import load_latest_answers


def test_load_latest_answers_returns_many(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "2026_a.json").write_text('{"question":"q1","answer":"a1","evaluation":{}}', encoding="utf-8")
    (reports_dir / "2026_b.json").write_text('{"question":"q2","answer":"a2","evaluation":{}}', encoding="utf-8")

    results = load_latest_answers(reports_dir, limit=5)

    assert len(results) == 2
    assert results[0]["answer"] in {"a1", "a2"}

