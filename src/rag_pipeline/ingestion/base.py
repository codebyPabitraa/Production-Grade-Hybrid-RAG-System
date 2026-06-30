from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag_pipeline.types import Document
from rag_pipeline.ingestion.router import extract_text


@dataclass(slots=True)
class IngestionResult:
    documents: list[Document]
    source_dir: Path


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".pdf",
    ".docx",
    ".html",
    ".htm",
    ".csv",
    ".xlsx",
    ".xlsm",
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".css",
    ".xml",
    ".sql",
}


def ingest_text_files(input_dir: Path) -> IngestionResult:
    documents: list[Document] = []

    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        extracted = extract_text(path)
        text = extracted.text
        if not text:
            continue
        documents.append(
            Document(
                doc_id=path.stem,
                text=text,
                metadata={
                    "path": str(path),
                    "extension": path.suffix.lower(),
                    **extracted.metadata,
                },
            )
        )

    return IngestionResult(documents=documents, source_dir=input_dir)
