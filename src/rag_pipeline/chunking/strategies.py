from __future__ import annotations

import re


def split_markdown_sections(text: str) -> list[str]:
    sections = re.split(r"(?m)^(#{1,6}\s+.+)$", text)
    combined: list[str] = []
    current = ""
    for part in sections:
        stripped = part.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            if current.strip():
                combined.append(current.strip())
            current = stripped
        else:
            current = f"{current}\n\n{stripped}" if current else stripped
    if current.strip():
        combined.append(current.strip())
    return combined if combined else [text.strip()]


def split_table_rows(text: str) -> list[str]:
    rows = [row.strip() for row in text.splitlines() if row.strip()]
    return rows if rows else [text.strip()]

