from pathlib import Path

from rag_pipeline.benchmark import load_questions, run_benchmark


def test_load_questions_supports_wrapped_questions(tmp_path: Path):
    path = tmp_path / "questions.json"
    path.write_text('{"questions": ["one", {"question": "two"}]}', encoding="utf-8")

    questions = load_questions(path)

    assert [item["question"] for item in questions] == ["one", "two"]


def test_run_benchmark_writes_summary(tmp_path: Path):
    questions_file = tmp_path / "questions.json"
    questions_file.write_text('["What is this about?"]', encoding="utf-8")
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "sample.txt").write_text("rag pipeline evaluation", encoding="utf-8")

    result = run_benchmark(
        questions_file,
        input_dir=raw_dir,
        chunk_size=100,
        chunk_overlap=10,
        top_k=2,
        report_dir=tmp_path / "reports",
    )

    assert result["run_count"] == 1
    assert result["answers"][0]["answer"]
    assert Path(result["summary_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    assert Path(result["markdown_path"]).read_text(encoding="utf-8").startswith("# Benchmark Summary")
