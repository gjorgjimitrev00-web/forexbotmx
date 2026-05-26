from __future__ import annotations

import argparse
from pathlib import Path

from forexbot.config import BotConfig, ConfigError, load_config
from forexbot.runtime import build_engine_from_config


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

    if args.command == "run":
        mode_error = _mode_error(config.mode, "run", {"paper", "mt5_demo", "mt5_live"})
        if mode_error is not None:
            print(mode_error)
            return 2

        if not args.once:
            print("run requires --once in V1")
            return 2

        return _run_engine(config, "journals/paper.jsonl", "paper summary")

    if args.command == "backtest":
        mode_error = _mode_error(config.mode, "backtest", "backtest")
        if mode_error is not None:
            print(mode_error)
            return 2

        return _run_engine(config, "journals/backtest.jsonl", "backtest summary")

    return 0


def _mode_error(mode: str, command: str, required_modes: str | set[str]) -> str | None:
    allowed = {required_modes} if isinstance(required_modes, str) else required_modes
    if mode in allowed:
        return None
    required = _format_required_modes(allowed)
    return f"{command} requires mode={required}; got mode={mode}"


def _run_engine(config: BotConfig, journal_path: str, summary_label: str) -> int:
    try:
        summary = build_engine_from_config(config, journal_path).run_once()
    except (OSError, KeyError, RuntimeError, ValueError) as exc:
        print(f"runtime error: {exc}")
        return 1

    print(f"{summary_label}: {summary}")
    if summary["errors"] > 0:
        return 1
    return 0


def _format_required_modes(modes: set[str]) -> str:
    ordered = [mode for mode in ("paper", "backtest", "mt5_demo", "mt5_live") if mode in modes]
    if len(ordered) == 1:
        return ordered[0]
    return f"{', '.join(ordered[:-1])}, or {ordered[-1]}"
