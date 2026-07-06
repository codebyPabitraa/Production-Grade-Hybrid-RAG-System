from rag_pipeline.generation import generate_answer
from rag_pipeline.retrieval.types import RetrievalResult
from rag_pipeline.types import Chunk


class _VerboseProvider:
    def generate(self, prompt):
        return (
            "This project answers questions from local files. "
            "It also uses evaluation reports to compare changes over time. "
            "It includes additional explanation that should be trimmed away."
        )


def test_generate_answer_uses_retrieved_context():
    chunk = Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25)
    result = RetrievalResult(chunk=chunk, score=1.0, rank=1)

    answer = generate_answer("What is the project about?", [result])

    assert "This project is about" in answer.answer
    assert "production rag pipeline" in answer.answer
    assert len(answer.answer.split()) < 80
    assert answer.sources[0].chunk.chunk_id == "a:0"


def test_generate_answer_trims_verbose_provider_output():
    chunk = Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25)
    result = RetrievalResult(chunk=chunk, score=1.0, rank=1)

    answer = generate_answer("What is the project about?", [result], provider=_VerboseProvider())

    assert len(answer.answer.split()) <= 90
    assert answer.answer.count(".") <= 3


def test_generate_answer_removes_dangling_meta_phrases():
    chunk = Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25)
    result = RetrievalResult(chunk=chunk, score=1.0, rank=1)

    answer = generate_answer(
        "Why do we save benchmark reports?",
        [result],
        provider=_VerboseProvider(),
    )

    assert "mentioned in ." not in answer.answer
    assert "stated in ." not in answer.answer
    assert "Reference:" not in answer.answer
