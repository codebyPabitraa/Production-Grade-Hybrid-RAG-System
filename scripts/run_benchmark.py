from __future__ import annotations

import argparse
import logging
from pathlib import Path

from rag_pipeline.benchmark import run_benchmark
from rag_pipeline.env import load_dotenv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a benchmark over multiple questions.")
    parser.add_argument("--questions-file", required=True, help="JSON file containing benchmark questions.")
    parser.add_argument("--input-dir", default="data/raw", help="Directory containing source documents.")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size for document splitting.")
    parser.add_argument("--chunk-overlap", type=int, default=120, help="Chunk overlap for document splitting.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks to use.")
    parser.add_argument("--report-dir", default="reports", help="Directory for saved evaluation reports.")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    result = run_benchmark(
        questions_file=Path(args.questions_file),
        input_dir=Path(args.input_dir),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        top_k=args.top_k,
        report_dir=Path(args.report_dir),
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
