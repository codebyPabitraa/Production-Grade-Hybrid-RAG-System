from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.benchmark_compare import compare_benchmarks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare two benchmark summary files.")
    parser.add_argument("--baseline", required=True, help="Path to the baseline benchmark_summary.json")
    parser.add_argument("--candidate", required=True, help="Path to the candidate benchmark_summary.json")
    parser.add_argument("--output-dir", default="reports", help="Directory for comparison output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = compare_benchmarks(Path(args.baseline), Path(args.candidate), output_dir=Path(args.output_dir))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

