from pathlib import Path

from rag_pipeline.ingestion.router import extract_text


def test_extract_text_unknown_extension_returns_empty(tmp_path: Path):
    path = tmp_path / "file.bin"
    path.write_bytes(b"abc")

    extracted = extract_text(path)
    assert extracted.text == ""
    assert extracted.metadata == {}
