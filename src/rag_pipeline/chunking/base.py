from __future__ import annotations

from rag_pipeline.types import Chunk, Document
from rag_pipeline.chunking.strategies import split_markdown_sections, split_table_rows


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
    return [paragraph for paragraph in paragraphs if paragraph]


def _window_text(text: str, chunk_size: int, chunk_overlap: int) -> list[tuple[int, int, str]]:
    windows: list[tuple[int, int, str]] = []
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk_text = text[start:end].strip()
        if chunk_text:
            windows.append((start, end, chunk_text))
        if end == len(text):
            break
        start = max(end - chunk_overlap, start + 1)

    return windows


def chunk_document(document: Document, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    text = document.text
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    index = 0

    kind = document.metadata.get("kind")
    if kind == "markdown":
        paragraphs = split_markdown_sections(text)
    elif kind in {"csv", "xlsx"}:
        paragraphs = split_table_rows(text)
    else:
        paragraphs = _split_paragraphs(text)

    if not paragraphs:
        return []

    cursor = 0
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            start = text.find(paragraph, cursor)
            end = start + len(paragraph)
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}:{index}",
                    doc_id=document.doc_id,
                    text=paragraph,
                    start=start,
                    end=end,
                    metadata=document.metadata.copy(),
                )
            )
            index += 1
            cursor = end
            continue

        start = text.find(paragraph, cursor)
        end = start + len(paragraph)
        for win_start, win_end, win_text in _window_text(paragraph, chunk_size, chunk_overlap):
            absolute_start = start + win_start
            absolute_end = start + win_end
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}:{index}",
                    doc_id=document.doc_id,
                    text=win_text,
                    start=absolute_start,
                    end=absolute_end,
                    metadata=document.metadata.copy(),
                )
            )
            index += 1
        cursor = end

    return chunks


def chunk_documents(documents: list[Document], chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, chunk_size, chunk_overlap))
    return chunks
