from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.benchmark_history import build_history_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a benchmark history index from saved reports.")
    parser.add_argument("--reports-dir", default="reports", help="Directory containing benchmark reports.")
    parser.add_argument("--output-path", default=None, help="Optional output path for the index JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = build_history_index(Path(args.reports_dir), Path(args.output_path) if args.output_path else None)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

