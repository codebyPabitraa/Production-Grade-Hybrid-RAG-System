from rag_pipeline.generation.prompt import build_prompt
from rag_pipeline.retrieval.types import RetrievalResult
from rag_pipeline.types import Chunk


def test_build_prompt_includes_context_blocks():
    chunk = Chunk(
        chunk_id="a:0",
        doc_id="a",
        text="production rag pipeline",
        start=0,
        end=25,
        metadata={"path": "data/raw/sample_project_notes.txt", "kind": "plain_text"},
    )
    result = RetrievalResult(chunk=chunk, score=0.91, rank=1)

    prompt = build_prompt("What is the project about?", [result])

    assert "Question:" in prompt.user_prompt
    assert "Context 1" in prompt.user_prompt
    assert prompt.metadata["context_count"] == 1

