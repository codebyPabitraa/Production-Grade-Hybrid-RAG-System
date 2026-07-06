from pathlib import Path

import json
from io import BytesIO

from rag_pipeline.app_server import _render_admin, _render_result, _render_user_dashboard, _send_json


def test_render_page_includes_form():
    html = _render_result()

    assert "RAG metrics explained" in html
    assert "Upload, approve, then ask" in html
    assert "Run RAG pipeline" in html
    assert "type=\"file\"" in html
    assert "BM25 results:" not in html
    assert "Retrieved context:" not in html
    assert "Not signed in" in html


def test_render_page_includes_results():
    html = _render_result(
        {
            "question": "What is this project about?",
            "answer": "Sample answer",
            "why_answer": "Grounded in the top retrieved chunk.",
            "report_path": "reports/sample.json",
            "documents": 2,
            "chunks": 4,
            "retrieval_results": 3,
            "context_precision": 0.1,
            "answer_relevancy": 0.2,
            "faithfulness": 0.3,
            "context_recall": 0.4,
        }
    )

    assert "Sample answer" in html
    assert "Why this answer" in html
    assert "Grounded in the top retrieved chunk." in html
    assert "Download JSON report" in html
    assert "BM25 results:" not in html
    assert "Retrieved context:" not in html


def test_render_page_shows_approved_browser(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from rag_pipeline.uploads import save_pending_upload, approve_upload

    record = save_pending_upload([("sample.txt", b"hello world")], question="Approved doc", notes="note")
    approve_upload(record.upload_id, review_note="approved")

    html = _render_result()

    assert "Approved corpus browser" not in html
    assert "sample.txt" not in html
    assert "Approved doc" not in html
    assert "Run RAG pipeline" in html


def test_render_page_shows_signed_in_user():
    html = _render_result(user={"role": "admin", "username": "Pabitra10", "email": "pabitrachakraborty4u@gmail.com"})

    assert "Signed in as" in html
    assert "Pabitra10" in html
    assert "Logout" in html
    assert "Dashboard" in html


def test_render_page_compacts_answer():
    html = _render_result({"answer": "A" * 600, "why_answer": "B" * 20})

    assert "A" * 420 in html
    assert "A" * 430 not in html


def test_render_user_dashboard_focuses_on_workspace(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from rag_pipeline.auth import save_question_history
    from rag_pipeline.uploads import save_pending_upload, approve_upload

    record = save_pending_upload(
        [("guide.pdf", b"pdf-bytes")],
        question="How does RAG work?",
        notes="approval",
        uploader_key="demo@example.com",
        uploader_username="demo",
        uploader_email="demo@example.com",
    )
    approve_upload(record.upload_id, review_note="approved")
    save_question_history(
        user_key="demo@example.com",
        username="demo",
        email="demo@example.com",
        question="How does RAG work?",
        answer="RAG combines retrieval and generation.",
        report_path="reports/sample.json",
        context_precision=0.2,
        answer_relevancy=0.3,
        faithfulness=0.4,
        context_recall=0.5,
    )

    html = _render_user_dashboard({"role": "user", "username": "demo", "email": "demo@example.com"})

    assert "User Dashboard" in html
    assert "Signed in as" in html
    assert "Open question page" in html
    assert "No raw JSON shown here" in html
    assert "My uploads" in html
    assert "How does RAG work?" in html
    assert "Recent questions and answers" in html
    assert "RAG combines retrieval and generation." in html
    assert "Search dashboard" in html
    assert "Delete" in html


def test_render_user_dashboard_filters_results(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from rag_pipeline.auth import save_question_history
    from rag_pipeline.uploads import save_pending_upload, approve_upload

    record = save_pending_upload([("alpha.pdf", b"alpha")], question="Alpha project", notes="one")
    approve_upload(record.upload_id, review_note="approved")
    save_question_history(
        user_key="demo@example.com",
        username="demo",
        email="demo@example.com",
        question="Alpha question",
        answer="Alpha answer",
        report_path="reports/a.json",
        context_precision=0.11,
        answer_relevancy=0.22,
        faithfulness=0.33,
        context_recall=0.44,
    )
    save_question_history(
        user_key="demo@example.com",
        username="demo",
        email="demo@example.com",
        question="Beta question",
        answer="Beta answer",
        report_path="reports/b.json",
        context_precision=0.55,
        answer_relevancy=0.66,
        faithfulness=0.77,
        context_recall=0.88,
    )

    html = _render_user_dashboard({"role": "user", "username": "demo", "email": "demo@example.com"}, search="Beta")

    assert "Beta question" in html
    assert "Alpha question" not in html
    assert "alpha.pdf" not in html
    assert "My uploads" in html


def test_render_admin_dashboard_includes_summary(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from rag_pipeline.uploads import save_pending_upload, approve_upload, reject_upload

    pending = save_pending_upload([("pending.txt", b"pending")], question="Pending doc", notes="awaiting review")
    approved = save_pending_upload([("approved.txt", b"approved")], question="Approved doc", notes="approved note")
    rejected = save_pending_upload([("rejected.txt", b"rejected")], question="Rejected doc", notes="reject note")
    approve_upload(approved.upload_id, review_note="looks good")
    reject_upload(rejected.upload_id, review_note="not needed")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "20260703T000001Z_admin.json").write_text(
        json.dumps(
            {
                "question": "Which metrics are tracked?",
                "answer": "Context precision, relevancy, faithfulness, and recall.",
                "evaluation": {"context_precision": 0.3},
            }
        ),
        encoding="utf-8",
    )

    html = _render_admin()

    assert "Admin upload queue" in html
    assert "Pending uploads" in html
    assert "Review summary" in html
    assert "File type breakdown" in html
    assert "Recent answered questions" in html
    assert "Which metrics are tracked?" in html
    assert "Pending" in html and "Approved" in html and "Rejected" in html


def test_render_admin_dashboard_filters_results(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from rag_pipeline.uploads import save_pending_upload

    save_pending_upload([("alpha.txt", b"alpha")], question="Alpha question", notes="first review")
    save_pending_upload([("beta.txt", b"beta")], question="Beta question", notes="second review")

    html = _render_admin(search="Beta")

    assert "Beta question" in html
    assert "Alpha question" not in html
    assert "Search admin queue" in html


def test_health_endpoint_returns_ok():
    class DummyHandler:
        def __init__(self):
            self.headers = {}
            self.status = None
            self.headers_sent = {}
            self.wfile = BytesIO()

        def send_response(self, status):
            self.status = status

        def send_header(self, key, value):
            self.headers_sent[key] = value

        def end_headers(self):
            pass

    handler = DummyHandler()
    _send_json(handler, {"status": "ok", "service": "rag-pipeline-demo"})
    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))

    assert handler.status == 200
    assert payload["status"] == "ok"
    assert payload["service"] == "rag-pipeline-demo"
