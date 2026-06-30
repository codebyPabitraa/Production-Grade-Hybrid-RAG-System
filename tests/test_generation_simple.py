from rag_pipeline.generation import generate_answer
from rag_pipeline.retrieval.types import RetrievalResult
from rag_pipeline.types import Chunk


def test_generate_answer_uses_retrieved_context():
    chunk = Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25)
    result = RetrievalResult(chunk=chunk, score=1.0, rank=1)

    answer = generate_answer("What is the project about?", [result])

    assert "This project is about" in answer.answer
    assert "production rag pipeline" in answer.answer
    assert len(answer.answer.split()) < 80
    assert answer.sources[0].chunk.chunk_id == "a:0"
