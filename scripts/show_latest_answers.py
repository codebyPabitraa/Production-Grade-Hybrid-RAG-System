from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.benchmark_history import load_latest_answers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show the latest saved answers from reports.")
    parser.add_argument("--reports-dir", default="reports", help="Directory containing report JSON files.")
    parser.add_argument("--limit", type=int, default=5, help="Number of answers to show.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    latest = load_latest_answers(Path(args.reports_dir), limit=args.limit)
    for item in latest:
        print(item["question"])
        print(item["answer"])
        print(item["report_path"])
        print("---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

