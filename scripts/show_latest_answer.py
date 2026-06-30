from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.benchmark_history import load_latest_answer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show the latest saved answer from reports.")
    parser.add_argument("--reports-dir", default="reports", help="Directory containing report JSON files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    latest = load_latest_answer(Path(args.reports_dir))
    print(latest["question"])
    print(latest["answer"])
    print(latest["report_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

