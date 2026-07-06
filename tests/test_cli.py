from pathlib import Path

from rag_pipeline.cli import format_retrieval_trace, run_cli
from rag_pipeline.retrieval.types import RetrievalResult
from rag_pipeline.types import Chunk


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
    assert result["retrieved_context"].startswith("Retrieved context:")
    assert "No retrieval results." in result["retrieved_context"]
    assert result["bm25_context"].startswith("BM25 results:")
    assert result["dense_context"].startswith("DENSE results:")


def test_format_retrieval_trace_includes_source_and_preview():
    chunk = Chunk(
        chunk_id="sample:0",
        doc_id="sample",
        text="This chunk explains how retrieval debugging works for the CLI output.",
        start=0,
        end=68,
        metadata={"path": "data/raw/sample.txt"},
    )
    result = RetrievalResult(chunk=chunk, score=0.42, rank=1, metadata={"strategy": "rrf"})

    trace = format_retrieval_trace([result], preview_chars=40)

    assert "Retrieved context:" in trace
    assert "source=data/raw/sample.txt" in trace
    assert "strategy=rrf" in trace
    assert "This chunk explains how retrieval" in trace
