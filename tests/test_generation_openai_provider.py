import os

import pytest

from rag_pipeline.generation.openai_provider import OpenAIProvider


def test_openai_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError):
        OpenAIProvider()

