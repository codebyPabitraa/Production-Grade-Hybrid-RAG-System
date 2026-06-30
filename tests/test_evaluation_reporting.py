from pathlib import Path

from rag_pipeline.evaluation import build_evaluation_report, save_evaluation_report
from rag_pipeline.evaluation.types import EvaluationResult
from rag_pipeline.generation.types import GeneratedAnswer


def test_save_evaluation_report_writes_json(tmp_path: Path):
    generated = GeneratedAnswer(question="q", answer="a")
    evaluation = EvaluationResult(
        context_precision=0.5,
        answer_relevancy=0.4,
        faithfulness=0.3,
        context_recall=0.2,
    )
    report = build_evaluation_report("q", generated, evaluation, documents=1, chunks=1, retrieval_results=1)

    path = save_evaluation_report(report, output_dir=tmp_path)

    assert path.exists()
    assert path.suffix == ".json"

