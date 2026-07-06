from __future__ import annotations

import os

from rag_pipeline.generation.prompt import PromptBundle
from rag_pipeline.generation.providers import AnswerProvider


class OpenAIProvider(AnswerProvider):
    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self._model = model
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to use OpenAIProvider")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("Install the 'openai' package to use OpenAIProvider") from exc

        self._client = OpenAI(api_key=api_key)

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
