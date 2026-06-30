from pathlib import Path

from rag_pipeline.benchmark import run_benchmark


def test_run_benchmark_supports_reference_answers(tmp_path: Path):
    questions_file = tmp_path / "questions.json"
    questions_file.write_text(
        '{"questions":[{"question":"What is this about?","reference_answer":"About a RAG pipeline."}]}',
        encoding="utf-8",
    )
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

    assert result["metrics"]["avg_reference_similarity"] >= 0.0

