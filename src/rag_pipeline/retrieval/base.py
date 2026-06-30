from __future__ import annotations

from abc import ABC, abstractmethod

from rag_pipeline.retrieval.types import RetrievalQuery, RetrievalResult


class Retriever(ABC):
    @abstractmethod
    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        raise NotImplementedError

