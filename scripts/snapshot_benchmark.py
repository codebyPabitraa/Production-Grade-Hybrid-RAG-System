from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.benchmark_compare import snapshot_latest_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Snapshot the latest benchmark summary into a folder.")
    parser.add_argument("--source", default="reports", help="Source benchmark summary file or directory.")
    parser.add_argument("--destination", required=True, help="Destination folder for the snapshot.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = snapshot_latest_summary(Path(args.source), Path(args.destination))
    print({"snapshot_path": str(path)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

