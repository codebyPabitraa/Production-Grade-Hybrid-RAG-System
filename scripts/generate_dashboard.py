from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline.dashboard import save_dashboard_html, save_report_pages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a static benchmark dashboard HTML file.")
    parser.add_argument("--reports-dir", default="reports", help="Directory containing benchmark reports.")
    parser.add_argument("--output", default=None, help="Path to write the dashboard HTML.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of recent runs to include.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reports_dir = Path(args.reports_dir)
    save_report_pages(reports_dir=reports_dir, limit=args.limit)
    path = save_dashboard_html(reports_dir, output_path=Path(args.output) if args.output else None, limit=args.limit)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
