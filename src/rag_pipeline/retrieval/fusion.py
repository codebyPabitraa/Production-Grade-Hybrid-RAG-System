from __future__ import annotations

from collections import defaultdict

from rag_pipeline.retrieval.types import RetrievalResult


def reciprocal_rank_fusion(result_sets: list[list[RetrievalResult]], k: int = 60) -> list[RetrievalResult]:
    fused_scores: dict[str, float] = defaultdict(float)
    chosen: dict[str, RetrievalResult] = {}

    for results in result_sets:
        for result in results:
            fused_scores[result.chunk.chunk_id] += 1.0 / (k + result.rank)
            chosen.setdefault(result.chunk.chunk_id, result)

    fused = [
        RetrievalResult(
            chunk=chosen[chunk_id].chunk,
            score=score,
            rank=0,
            metadata={**chosen[chunk_id].metadata, "strategy": "rrf"},
        )
        for chunk_id, score in fused_scores.items()
    ]
    fused.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
    for index, result in enumerate(fused, start=1):
        result.rank = index
    return fused

