from pathlib import Path
import json

from rag_pipeline.dashboard import build_dashboard_html, save_dashboard_html


def test_build_dashboard_html_includes_title(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_path = reports_dir / "20260702T000000Z_sample.json"
    report_path.write_text(
        json.dumps(
            {
                "question": "What is this project about?",
                "report_path": str(report_path),
                "summary": {},
                "evaluation": {
                    "context_precision": 0.1,
                    "answer_relevancy": 0.2,
                    "faithfulness": 0.3,
                    "context_recall": 0.4,
                },
            }
        ),
        encoding="utf-8",
    )
    html = build_dashboard_html(reports_dir=reports_dir)

    assert "RAG Benchmark Dashboard" in html
    assert "What is this project about?" in html
    assert "class=\"bar\"" in html
    assert "class=\"trend" in html
    assert "Selected Run" in html
    assert "detail-question" in html
    assert "run-search" in html
    assert "context-toggle" in html
    assert "copy-answer" in html
    assert "Open report" in html
    assert "Download" in html
    assert "report-pages/" in html
    assert "setActiveRow" in html
    assert "classList.toggle(\"active\"" in html
    assert "metric-list" in html
    assert "metric-pill" in html


def test_save_dashboard_html_writes_file(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    output = save_dashboard_html(reports_dir=reports_dir)

    assert output.exists()
    assert output.name == "benchmark_dashboard.html"


def test_dashboard_uses_generated_sources_for_context(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_path = reports_dir / "20260702T000001Z_sample.json"
    report_path.write_text(
        json.dumps(
            {
                "timestamp_utc": "2026-07-02T00:00:01Z",
                "question": "What is this project about?",
                "answer": "Sample answer",
                "generated": {
                    "sources": [
                        {
                            "chunk": {
                                "text": "This is the retrieved context.",
                                "doc_id": "sample",
                                "metadata": {"path": "data/raw/sample.txt"},
                            }
                        }
                    ]
                },
                "evaluation": {
                    "context_precision": 0.1,
                    "answer_relevancy": 0.2,
                    "faithfulness": 0.3,
                    "context_recall": 0.4,
                },
            }
        ),
        encoding="utf-8",
    )

    html = build_dashboard_html(reports_dir=reports_dir)

    assert "This is the retrieved context." in html
    assert "data/raw/sample.txt" not in html


def test_build_report_page_html_includes_answer_and_context(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_path = reports_dir / "20260702T000001Z_sample.json"
    report_path.write_text(
        json.dumps(
            {
                "timestamp_utc": "2026-07-02T00:00:01Z",
                "question": "What is this project about?",
                "answer": "Sample answer",
                "generated": {
                    "sources": [
                        {
                            "chunk": {
                                "text": "This is the retrieved context.",
                                "doc_id": "sample",
                                "metadata": {"path": "data/raw/sample.txt"},
                            }
                        }
                    ]
                },
                "evaluation": {
                    "context_precision": 0.1,
                    "answer_relevancy": 0.2,
                    "faithfulness": 0.3,
                    "context_recall": 0.4,
                },
            }
        ),
        encoding="utf-8",
    )

    from rag_pipeline.dashboard import build_report_page_html

    html = build_report_page_html(report_path)

    assert "Run Report" in html
    assert "Sample answer" in html
    assert "This is the retrieved context." in html
    assert "Context Precision" in html
    assert "../benchmark_dashboard.html" in html
    assert "Download HTML" in html
    assert "#metrics" in html
    assert "#answer" in html
    assert "#context" in html
    assert "Retrieved sources" in html
