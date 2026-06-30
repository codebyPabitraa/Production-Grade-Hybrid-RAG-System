from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.benchmark_history import latest_benchmark_history_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show a compact benchmark history table.")
    parser.add_argument("--reports-dir", default="reports", help="Directory containing benchmark reports.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of rows to show.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(latest_benchmark_history_table(Path(args.reports_dir), limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

