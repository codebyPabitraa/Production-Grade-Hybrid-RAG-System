from rag_pipeline.retrieval import RetrievalOrchestrator, RetrievalQuery
from rag_pipeline.types import Chunk


def test_retrieval_orchestrator_returns_fused_ranked_results():
    chunks = [
        Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25),
        Chunk(chunk_id="b:0", doc_id="b", text="random text only", start=0, end=16),
        Chunk(chunk_id="c:0", doc_id="c", text="rag pipeline evaluation", start=0, end=23),
    ]

    orchestrator = RetrievalOrchestrator(chunks)
    results = orchestrator.search(RetrievalQuery(query="rag pipeline", top_k=2))

    assert len(results) == 2
    assert results[0].rank == 1


def test_retrieval_orchestrator_exposes_components():
    chunks = [
        Chunk(chunk_id="a:0", doc_id="a", text="production rag pipeline", start=0, end=25),
        Chunk(chunk_id="b:0", doc_id="b", text="random text only", start=0, end=16),
    ]

    orchestrator = RetrievalOrchestrator(chunks)
    components = orchestrator.search_components(RetrievalQuery(query="rag pipeline", top_k=2))

    assert set(components) == {"bm25", "dense"}
    assert len(components["bm25"]) >= 1
    assert len(components["dense"]) >= 1
