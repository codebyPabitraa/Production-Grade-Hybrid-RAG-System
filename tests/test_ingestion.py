from pathlib import Path

from rag_pipeline.ingestion import ingest_text_files


def test_ingest_text_files_supports_txt_and_md(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    (raw_dir / "one.txt").write_text("hello txt", encoding="utf-8")
    (raw_dir / "two.md").write_text("hello md", encoding="utf-8")
    (raw_dir / "three.csv").write_text("a,b\n1,2", encoding="utf-8")
    (raw_dir / "ignore.bin").write_bytes(b"skip me")

    result = ingest_text_files(raw_dir)

    assert len(result.documents) == 3
    assert {doc.metadata["extension"] for doc in result.documents} == {".txt", ".md", ".csv"}
    assert all("path" in doc.metadata for doc in result.documents)
