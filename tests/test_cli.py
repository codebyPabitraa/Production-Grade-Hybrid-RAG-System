from pathlib import Path

from rag_pipeline.cli import run_cli


def test_run_cli_returns_report(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "sample.txt").write_text("rag pipeline evaluation", encoding="utf-8")

    result = run_cli(
        question="What is this about?",
        input_dir=raw_dir,
        chunk_size=100,
        chunk_overlap=10,
        top_k=2,
        report_dir=tmp_path / "reports",
    )

    assert result["documents"] == 1
    assert Path(result["report_path"]).exists()

