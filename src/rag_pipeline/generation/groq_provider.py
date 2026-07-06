from __future__ import annotations

import os

from rag_pipeline.generation.prompt import PromptBundle
from rag_pipeline.generation.providers import AnswerProvider


class GroqProvider(AnswerProvider):
    def __init__(self, model: str | None = None) -> None:
        self._model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is required to use GroqProvider")

        try:
            from groq import Groq
        except ImportError as exc:
            raise ImportError("Install the 'groq' package to use GroqProvider") from exc

        self._client = Groq(api_key=api_key)

    def generate(self, prompt: PromptBundle) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        message = response.choices[0].message.content or ""
        return message.strip()
