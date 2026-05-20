from __future__ import annotations

import argparse
from pathlib import Path

from forexbot.broker import PaperBroker
from forexbot.config import BotConfig, ConfigError, load_config
from forexbot.engine import TradingEngine
from forexbot.journal import JsonlJournal
from forexbot.market_data import JsonMarketDataProvider
from forexbot.risk import RiskManager
from forexbot.strategy import TrendFollowingStrategy


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
        if not args.once:
            print("run requires --once in V1")
            return 2

        summary = _build_engine(config, "journals/paper.jsonl").run_once()
        print(f"paper summary: {summary}")
        return 0

    if args.command == "backtest":
        summary = _build_engine(config, "journals/backtest.jsonl").run_once()
        print(f"backtest summary: {summary}")
        return 0

    return 0


def _build_engine(config: BotConfig, journal_path: str) -> TradingEngine:
    return TradingEngine(
        symbols=tuple(config.symbols),
        market_data=JsonMarketDataProvider(config.market_data.path),
        strategy=TrendFollowingStrategy(config.strategy),
        risk_manager=RiskManager(config.risk),
        broker=PaperBroker(config.account.starting_equity),
        journal=JsonlJournal(journal_path),
        spread_points={
            symbol.name: min(config.strategy.max_spread_points, 10)
            for symbol in config.symbols
        },
    )
