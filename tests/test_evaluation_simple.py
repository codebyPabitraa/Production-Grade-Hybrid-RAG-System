from rag_pipeline.evaluation import evaluate_answer
from rag_pipeline.generation.types import GeneratedAnswer
from rag_pipeline.retrieval.types import RetrievalResult
from rag_pipeline.types import Chunk


def test_evaluate_answer_returns_scores():
    chunk = Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25)
    retrieval = RetrievalResult(chunk=chunk, score=1.0, rank=1)
    answer = GeneratedAnswer(
        question="What is the project about?",
        answer="This project is about a production rag pipeline.",
        sources=[retrieval],
    )

    result = evaluate_answer("What is the project about?", answer, [retrieval])

    assert 0.0 <= result.answer_relevancy <= 1.0
    assert 0.0 <= result.faithfulness <= 1.0
    assert 0.0 <= result.context_precision <= 1.0
    assert 0.0 <= result.context_recall <= 1.0

