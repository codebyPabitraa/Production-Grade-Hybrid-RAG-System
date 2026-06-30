from __future__ import annotations

from collections import Counter
import math

from rag_pipeline.retrieval.base import Retriever
from rag_pipeline.retrieval.tokenize import tokenize
from rag_pipeline.retrieval.types import RetrievalQuery, RetrievalResult
from rag_pipeline.types import Chunk


def _vectorize(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(left[token] * right.get(token, 0) for token in left)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


class DenseRetriever(Retriever):
    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._vectors = {chunk.chunk_id: _vectorize(chunk.text) for chunk in chunks}

    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        query_vector = _vectorize(query.query)
        results: list[RetrievalResult] = []
        for chunk in self._chunks:
            score = _cosine_similarity(query_vector, self._vectors[chunk.chunk_id])
            if score > 0:
                results.append(
                    RetrievalResult(chunk=chunk, score=score, rank=0, metadata={"strategy": "dense"})
                )
        results.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
        for index, result in enumerate(results, start=1):
            result.rank = index
        return results[: query.top_k]

