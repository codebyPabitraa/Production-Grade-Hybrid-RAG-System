from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_pipeline.storage import uploads_root


UPLOAD_ROOT = uploads_root()
PENDING_DIR = UPLOAD_ROOT / "pending"
APPROVED_DIR = UPLOAD_ROOT / "approved"
REJECTED_DIR = UPLOAD_ROOT / "rejected"


@dataclass(slots=True)
class UploadRecord:
    upload_id: str
    created_utc: str
    question: str
    notes: str
    files: list[str]
    status: str = "pending"
    review_note: str = ""
    uploader_key: str = ""
    uploader_username: str = ""
    uploader_email: str = ""


def _record_path(base_dir: Path, upload_id: str) -> Path:
    return base_dir / upload_id / "manifest.json"


def ensure_upload_dirs() -> None:
    for path in [PENDING_DIR, APPROVED_DIR, REJECTED_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def save_pending_upload(
    files: list[tuple[str, bytes]],
    question: str,
    notes: str = "",
    uploader_key: str = "",
    uploader_username: str = "",
    uploader_email: str = "",
) -> UploadRecord:
    ensure_upload_dirs()
    upload_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_{uuid.uuid4().hex[:8]}"
    upload_dir = PENDING_DIR / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_files: list[str] = []
    for filename, payload in files:
        target = upload_dir / Path(filename).name
        target.write_bytes(payload)
        saved_files.append(target.name)
    record = UploadRecord(
        upload_id=upload_id,
        created_utc=datetime.now(timezone.utc).isoformat(),
        question=question,
        notes=notes,
        files=saved_files,
        uploader_key=uploader_key,
        uploader_username=uploader_username,
        uploader_email=uploader_email,
    )
    _record_path(PENDING_DIR, upload_id).write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
    return record


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid manifest")
    return data


def list_uploads(status: str = "pending") -> list[dict[str, Any]]:
    ensure_upload_dirs()
    base = {
        "pending": PENDING_DIR,
        "approved": APPROVED_DIR,
        "rejected": REJECTED_DIR,
    }[status]
    uploads: list[dict[str, Any]] = []
    for manifest in sorted(base.glob("*/manifest.json"), reverse=True):
        try:
            data = _load_manifest(manifest)
        except Exception:
            continue
        data["manifest_path"] = str(manifest)
        uploads.append(data)
    return uploads


def list_user_uploads(status: str, user_key: str) -> list[dict[str, Any]]:
    uploads = list_uploads(status=status)
    return [item for item in uploads if item.get("uploader_key") == user_key]


def approve_upload(upload_id: str, review_note: str = "") -> dict[str, Any]:
    ensure_upload_dirs()
    pending_manifest = _record_path(PENDING_DIR, upload_id)
    if not pending_manifest.exists():
        raise FileNotFoundError(upload_id)
    pending_dir = pending_manifest.parent
    approved_dir = APPROVED_DIR / upload_id
    approved_dir.mkdir(parents=True, exist_ok=True)
    for item in pending_dir.iterdir():
        shutil.move(str(item), str(approved_dir / item.name))
    pending_dir.rmdir()
    manifest = _load_manifest(approved_dir / "manifest.json")
    manifest["status"] = "approved"
    manifest["review_note"] = review_note
    (approved_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def get_upload(upload_id: str, status: str = "pending") -> dict[str, Any]:
    ensure_upload_dirs()
    base = {
        "pending": PENDING_DIR,
        "approved": APPROVED_DIR,
        "rejected": REJECTED_DIR,
    }[status]
    manifest = base / upload_id / "manifest.json"
    if not manifest.exists():
        raise FileNotFoundError(upload_id)
    return _load_manifest(manifest)


def reject_upload(upload_id: str, review_note: str = "") -> dict[str, Any]:
    ensure_upload_dirs()
    pending_manifest = _record_path(PENDING_DIR, upload_id)
    if not pending_manifest.exists():
        raise FileNotFoundError(upload_id)
    pending_dir = pending_manifest.parent
    rejected_dir = REJECTED_DIR / upload_id
    rejected_dir.mkdir(parents=True, exist_ok=True)
    for item in pending_dir.iterdir():
        shutil.move(str(item), str(rejected_dir / item.name))
    pending_dir.rmdir()
    manifest = _load_manifest(rejected_dir / "manifest.json")
    manifest["status"] = "rejected"
    manifest["review_note"] = review_note
    (rejected_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def list_approved_files() -> list[dict[str, Any]]:
    ensure_upload_dirs()
    files: list[dict[str, Any]] = []
    for manifest in sorted(APPROVED_DIR.glob("*/manifest.json"), reverse=True):
        try:
            data = _load_manifest(manifest)
        except Exception:
            continue
        upload_dir = manifest.parent
        for name in data.get("files", []):
            file_path = upload_dir / name
            if not file_path.exists():
                continue
            files.append(
                {
                    "upload_id": data.get("upload_id", ""),
                    "question": data.get("question", ""),
                    "file_name": name,
                    "path": str(file_path),
                    "created_utc": data.get("created_utc", ""),
                    "review_note": data.get("review_note", ""),
                }
            )
    return files


def upload_file_type_breakdown(status: str = "pending") -> list[dict[str, Any]]:
    ensure_upload_dirs()
    uploads = list_uploads(status=status)
    counts: dict[str, int] = {}
    for upload in uploads:
        for filename in upload.get("files", []):
            suffix = Path(str(filename)).suffix.lower().lstrip(".") or "no_extension"
            counts[suffix] = counts.get(suffix, 0) + 1
    breakdown = [{"file_type": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    return breakdown


def approved_input_dir() -> Path:
    ensure_upload_dirs()
    return APPROVED_DIR
