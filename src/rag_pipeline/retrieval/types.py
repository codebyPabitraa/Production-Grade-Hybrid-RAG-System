from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag_pipeline.types import Chunk


@dataclass(slots=True)
class RetrievalResult:
    chunk: Chunk
    score: float
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalQuery:
    query: str
    top_k: int = 5

