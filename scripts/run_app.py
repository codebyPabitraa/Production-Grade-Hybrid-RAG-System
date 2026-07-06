from __future__ import annotations

import argparse

from rag_pipeline.app_server import serve_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local upload-and-ask RAG demo.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the demo server.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the demo server.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    serve_demo(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
