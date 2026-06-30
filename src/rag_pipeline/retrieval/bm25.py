from __future__ import annotations

from collections import Counter
import math

from rag_pipeline.retrieval.base import Retriever
from rag_pipeline.retrieval.tokenize import tokenize
from rag_pipeline.retrieval.types import RetrievalQuery, RetrievalResult
from rag_pipeline.types import Chunk


class BM25Retriever(Retriever):
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self._chunks = chunks
        self._k1 = k1
        self._b = b
        self._token_counts = [Counter(tokenize(chunk.text)) for chunk in chunks]
        self._doc_lengths = [sum(counts.values()) for counts in self._token_counts]
        self._avgdl = sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        self._df: Counter[str] = Counter()
        for counts in self._token_counts:
            self._df.update(counts.keys())
        self._n = len(chunks)

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        return math.log(1 + ((self._n - df + 0.5) / (df + 0.5))) if df else 0.0

    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        query_terms = tokenize(query.query)
        results: list[RetrievalResult] = []

        for chunk, counts, doc_len in zip(self._chunks, self._token_counts, self._doc_lengths):
            score = 0.0
            for term in query_terms:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                idf = self._idf(term)
                denom = tf + self._k1 * (1 - self._b + self._b * (doc_len / self._avgdl if self._avgdl else 0.0))
                score += idf * ((tf * (self._k1 + 1)) / denom)
            if score > 0:
                results.append(
                    RetrievalResult(chunk=chunk, score=score, rank=0, metadata={"strategy": "bm25"})
                )

        results.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
        for index, result in enumerate(results, start=1):
            result.rank = index
        return results[: query.top_k]

