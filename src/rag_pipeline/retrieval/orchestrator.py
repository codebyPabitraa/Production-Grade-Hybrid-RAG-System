from __future__ import annotations

from rag_pipeline.retrieval.bm25 import BM25Retriever
from rag_pipeline.retrieval.dense import DenseRetriever
from rag_pipeline.retrieval.fusion import reciprocal_rank_fusion
from rag_pipeline.retrieval.types import RetrievalQuery, RetrievalResult
from rag_pipeline.types import Chunk


class RetrievalOrchestrator:
    def __init__(self, chunks: list[Chunk]) -> None:
        self._bm25 = BM25Retriever(chunks)
        self._dense = DenseRetriever(chunks)

    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        bm25_results = self._bm25.search(query)
        dense_results = self._dense.search(query)
        return reciprocal_rank_fusion([bm25_results, dense_results])[: query.top_k]

