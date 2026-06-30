from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EvaluationResult:
    context_precision: float
    answer_relevancy: float
    faithfulness: float
    context_recall: float
    reference_similarity: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
