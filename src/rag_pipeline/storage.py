from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    return Path(os.getenv("RAG_DATA_DIR", "data"))


def reports_root() -> Path:
    return Path(os.getenv("RAG_REPORTS_DIR", "reports"))


def auth_root() -> Path:
    return data_root() / "auth"


def uploads_root() -> Path:
    return data_root() / "uploads"


def raw_data_root() -> Path:
    return data_root() / "raw"


def processed_data_root() -> Path:
    return data_root() / "processed"

