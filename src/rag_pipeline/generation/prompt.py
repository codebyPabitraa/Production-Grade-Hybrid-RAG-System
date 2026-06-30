from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag_pipeline.retrieval.types import RetrievalResult


@dataclass(slots=True)
class PromptBundle:
    question: str
    system_prompt: str
    user_prompt: str
    context_blocks: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def build_prompt(question: str, retrieved_context: list[RetrievalResult]) -> PromptBundle:
    top_chunks = retrieved_context[:3]
    context_blocks: list[str] = []
    for index, result in enumerate(top_chunks, start=1):
        path = result.chunk.metadata.get("path", "unknown")
        kind = result.chunk.metadata.get("kind", result.chunk.metadata.get("extension", "unknown"))
        score = f"{result.score:.4f}"
        context_blocks.append(
            f"[Context {index}] source={path} kind={kind} score={score}\n"
            f"chunk_id={result.chunk.chunk_id}\n"
            f"{result.chunk.text}"
        )

    system_prompt = (
        "You are a precise RAG assistant. Use only the provided context. "
        "Synthesize the answer in clear prose. If the context is insufficient, say so clearly. "
        "Prefer direct factual statements, answer the question explicitly in the first sentence, "
        "and reference the relevant context blocks. Keep answers concise: 2-4 sentences max."
    )
    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Instructions:\n"
        f"- Answer the question directly in the first sentence.\n"
        f"- Use the question's key terms naturally in the answer.\n"
        f"- Be concise but complete: 2-4 sentences max.\n"
        f"- Mention uncertainty when the context does not support a claim.\n\n"
        "Context:\n"
        + "\n\n".join(context_blocks)
        if context_blocks
        else f"Question:\n{question}\n\nContext:\nNo relevant context was retrieved."
    )

    return PromptBundle(
        question=question,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        context_blocks=context_blocks,
        metadata={"strategy": "prompt_template", "context_count": len(context_blocks)},
    )
