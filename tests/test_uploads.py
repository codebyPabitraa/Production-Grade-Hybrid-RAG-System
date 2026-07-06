from pathlib import Path

from rag_pipeline.uploads import approve_upload, get_upload, list_uploads, reject_upload, save_pending_upload


def test_upload_approval_lifecycle(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    record = save_pending_upload([("sample.txt", b"hello world")], question="Sample upload", notes="note")
    pending = list_uploads("pending")
    assert pending and pending[0]["upload_id"] == record.upload_id

    manifest = approve_upload(record.upload_id, review_note="Looks good")
    assert manifest["status"] == "approved"
    assert manifest["review_note"] == "Looks good"
    assert get_upload(record.upload_id, "approved")["status"] == "approved"
    assert list_uploads("pending") == []
    approved = list_uploads("approved")
    assert approved and approved[0]["status"] == "approved"
    assert (Path("data/uploads/approved") / record.upload_id / "sample.txt").exists()


def test_reject_upload_moves_record(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    record = save_pending_upload([("sample.txt", b"hello world")], question="Sample upload", notes="note")
    manifest = reject_upload(record.upload_id, review_note="Not relevant")
    assert manifest["status"] == "rejected"
    assert manifest["review_note"] == "Not relevant"
    assert get_upload(record.upload_id, "rejected")["status"] == "rejected"
    assert list_uploads("pending") == []
    assert list_uploads("rejected")
