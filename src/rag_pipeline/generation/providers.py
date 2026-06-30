from __future__ import annotations

from abc import ABC, abstractmethod

from rag_pipeline.generation.prompt import PromptBundle


class AnswerProvider(ABC):
    @abstractmethod
    def generate(self, prompt: PromptBundle) -> str:
        raise NotImplementedError

