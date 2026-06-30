from __future__ import annotations

from pathlib import Path

from rag_pipeline.config import PipelineConfig
from rag_pipeline.logging import setup_logging
from rag_pipeline.pipeline import run_baseline_pipeline


def main() -> None:
    setup_logging()
    config = PipelineConfig.from_yaml(Path("configs/pipeline.yaml"))
    result = run_baseline_pipeline(config)
    print(result)


if __name__ == "__main__":
    main()
