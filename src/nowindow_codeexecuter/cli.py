from __future__ import annotations

import argparse
import json
import sys

from .executor import ExecutionRequest, execute_code
from .server import run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nwe", description="NoWindow Code Executer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cmd = subparsers.add_parser("run", help="Run code snippet")
    run_cmd.add_argument("--language", required=True, help="python|javascript|bash")
    run_cmd.add_argument("--code", required=True, help="Code snippet to execute")
    run_cmd.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds")

    serve_cmd = subparsers.add_parser("serve", help="Start HTTP server")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8080)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        request = ExecutionRequest(
            language=args.language,
            code=args.code,
            timeout_seconds=args.timeout,
        )
        try:
            result = execute_code(request)
        except Exception as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    if args.command == "serve":
        run_server(args.host, args.port)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
