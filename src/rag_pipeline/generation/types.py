from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag_pipeline.generation.prompt import PromptBundle
from rag_pipeline.retrieval.types import RetrievalResult


@dataclass(slots=True)
class GeneratedAnswer:
    question: str
    answer: str
    sources: list[RetrievalResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    prompt: PromptBundle | None = None
