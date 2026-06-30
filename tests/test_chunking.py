from rag_pipeline.chunking import chunk_document
from rag_pipeline.types import Document


def test_chunk_document_preserves_paragraphs():
    document = Document(
        doc_id="doc1",
        text="first paragraph\n\nsecond paragraph",
    )
    chunks = chunk_document(document, chunk_size=100, chunk_overlap=10)
    assert len(chunks) == 2
    assert chunks[0].text == "first paragraph"
    assert chunks[1].text == "second paragraph"


def test_chunk_document_falls_back_to_windowing_for_long_paragraphs():
    document = Document(
        doc_id="doc2",
        text="abcdefghij",
    )
    chunks = chunk_document(document, chunk_size=4, chunk_overlap=1)
    assert len(chunks) >= 2
    assert chunks[0].text == "abcd"
