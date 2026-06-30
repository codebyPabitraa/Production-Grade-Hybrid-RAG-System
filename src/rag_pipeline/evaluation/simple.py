from __future__ import annotations

import re

from rag_pipeline.evaluation.types import EvaluationResult
from rag_pipeline.generation.types import GeneratedAnswer
from rag_pipeline.retrieval.types import RetrievalResult

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "we",
    "what",
    "when",
    "which",
    "with",
    "you",
}


def _tokenize(text: str) -> set[str]:
    normalized = text.lower()
    normalized = normalized.replace("rag", "retrieval augmented generation")
    normalized = normalized.replace("llm", "large language model")
    normalized = normalized.replace("bm25", "bm twenty five")
    normalized = normalized.replace("pdf", "portable document format")
    normalized = normalized.replace("docx", "word document")
    normalized = normalized.replace("xlsx", "excel spreadsheet")
    return {token for token in re.findall(r"[a-z0-9]+", normalized) if token not in _STOPWORDS}


def _overlap_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _f1_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    precision = overlap / len(left)
    recall = overlap / len(right)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _first_sentence(text: str) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return sentence.strip()


def evaluate_answer(question: str, answer: GeneratedAnswer, retrieved_context: list[RetrievalResult]) -> EvaluationResult:
    question_tokens = _tokenize(question)
    answer_tokens = _tokenize(answer.answer)

    context_tokens: set[str] = set()
    for result in retrieved_context:
        context_tokens |= _tokenize(result.chunk.text)

    context_precision = 0.0
    if retrieved_context:
        scores = []
        for result in retrieved_context:
            chunk_tokens = _tokenize(result.chunk.text)
            scores.append(_overlap_score(answer_tokens, chunk_tokens))
        context_precision = sum(scores) / len(scores) if scores else 0.0

    answer_sentence_tokens = _tokenize(_first_sentence(answer.answer))
    answer_relevancy = 0.7 * _f1_score(question_tokens, answer_sentence_tokens) + 0.3 * _overlap_score(question_tokens, answer_tokens)
    faithfulness = _overlap_score(answer_tokens, context_tokens)
    context_recall = _overlap_score(question_tokens, context_tokens)

    return EvaluationResult(
        context_precision=context_precision,
        answer_relevancy=answer_relevancy,
        faithfulness=faithfulness,
        context_recall=context_recall,
        reference_similarity=0.0,
        metadata={"strategy": "heuristic_overlap"},
    )


def evaluate_against_reference(answer_text: str, reference_text: str | None) -> float:
    if not reference_text:
        return 0.0
    return _f1_score(_tokenize(answer_text), _tokenize(reference_text))
