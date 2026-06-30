from __future__ import annotations

from pathlib import Path

import yaml

from pydantic import BaseModel, Field


class IngestionConfig(BaseModel):
    input_dir: Path = Path("data/raw")
    output_dir: Path = Path("data/processed")


class ChunkingConfig(BaseModel):
    chunk_size: int = Field(default=800, ge=100)
    chunk_overlap: int = Field(default=120, ge=0)


class PipelineConfig(BaseModel):
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "PipelineConfig":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate(data)
