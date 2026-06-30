from __future__ import annotations

from pathlib import Path

from rag_pipeline.ingestion.extractors import (
    extract_text_from_code,
    extract_text_from_csv,
    extract_text_from_docx,
    extract_text_from_html,
    extract_text_from_md,
    extract_text_from_pdf,
    extract_text_from_txt,
    extract_text_from_xlsx,
)
from rag_pipeline.ingestion.schema import ExtractedContent


def extract_text(path: Path) -> ExtractedContent:
    suffix = path.suffix.lower()
    if suffix in {".txt"}:
        return extract_text_from_txt(path)
    if suffix in {".md", ".markdown"}:
        return extract_text_from_md(path)
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    if suffix in {".html", ".htm"}:
        return extract_text_from_html(path)
    if suffix == ".csv":
        return extract_text_from_csv(path)
    if suffix in {".xlsx", ".xlsm"}:
        return extract_text_from_xlsx(path)
    if suffix in {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".css", ".xml", ".sql"}:
        return extract_text_from_code(path)
    return ExtractedContent(text="", metadata={})
