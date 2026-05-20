from __future__ import annotations

import argparse
from pathlib import Path

from forexbot.config import ConfigError, load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forexbot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_config = subparsers.add_parser("check-config", help="Validate a bot config file.")
    check_config.add_argument("--config", required=True)

    run = subparsers.add_parser("run", help="Run the bot.")
    run.add_argument("--config", required=True)
    run.add_argument("--once", action="store_true", help="Run one cycle and exit.")

    backtest = subparsers.add_parser("backtest", help="Run a deterministic local backtest.")
    backtest.add_argument("--config", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(Path(args.config))
    except (ConfigError, OSError, KeyError, ValueError) as exc:
        print(f"config error: {exc}")
        return 2

    if args.command == "check-config":
        print(f"OK: {args.config} mode={config.mode} symbols={len(config.symbols)}")
        return 0

    print(f"{args.command} command is available for mode={config.mode}; engine wiring is added in Task 8.")
    return 0
