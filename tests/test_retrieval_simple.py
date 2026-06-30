from rag_pipeline.retrieval import KeywordRetriever, RetrievalQuery
from rag_pipeline.types import Chunk


def test_keyword_retriever_returns_ranked_matches():
    chunks = [
        Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25),
        Chunk(chunk_id="b:0", doc_id="b", text="random text only", start=0, end=16),
        Chunk(chunk_id="c:0", doc_id="c", text="rag pipeline evaluation", start=0, end=23),
    ]

    retriever = KeywordRetriever(chunks)
    results = retriever.search(RetrievalQuery(query="rag pipeline", top_k=2))

    assert len(results) == 2
    assert results[0].chunk.chunk_id == "a:0"
    assert results[0].rank == 1
    assert results[1].rank == 2

