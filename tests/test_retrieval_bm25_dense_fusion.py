from rag_pipeline.retrieval import BM25Retriever, DenseRetriever, RetrievalQuery, reciprocal_rank_fusion
from rag_pipeline.types import Chunk


def _chunks() -> list[Chunk]:
    return [
        Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25),
        Chunk(chunk_id="b:0", doc_id="b", text="random text only", start=0, end=16),
        Chunk(chunk_id="c:0", doc_id="c", text="rag pipeline evaluation", start=0, end=23),
    ]


def test_bm25_returns_ranked_matches():
    retriever = BM25Retriever(_chunks())
    results = retriever.search(RetrievalQuery(query="rag pipeline", top_k=2))
    assert len(results) == 2
    assert results[0].rank == 1


def test_dense_returns_ranked_matches():
    retriever = DenseRetriever(_chunks())
    results = retriever.search(RetrievalQuery(query="rag pipeline", top_k=2))
    assert len(results) == 2
    assert results[0].rank == 1


def test_rrf_combines_results():
    bm25_results = BM25Retriever(_chunks()).search(RetrievalQuery(query="rag pipeline", top_k=2))
    dense_results = DenseRetriever(_chunks()).search(RetrievalQuery(query="rag pipeline", top_k=2))
    fused = reciprocal_rank_fusion([bm25_results, dense_results])
    assert fused
    assert fused[0].rank == 1

