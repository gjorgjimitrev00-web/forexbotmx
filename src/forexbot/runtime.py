from __future__ import annotations

from pathlib import Path
from typing import Any

from forexbot.broker import PaperBroker
from forexbot.config import BotConfig
from forexbot.engine import TradingEngine
from forexbot.journal import JsonlJournal
from forexbot.market_data import JsonMarketDataProvider
from forexbot.mt5_broker import MT5Broker
from forexbot.mt5_market_data import MT5MarketDataProvider
from forexbot.risk import RiskManager
from forexbot.strategy import TrendFollowingStrategy


def build_engine_from_config(
    config: BotConfig,
    journal_path: str | Path,
    *,
    mt5_module: Any | None = None,
) -> TradingEngine:
    if config.mode in {"paper", "backtest"}:
        broker = PaperBroker(config.account.starting_equity)
        market_data = JsonMarketDataProvider(config.market_data.path)
    elif config.mode in {"mt5_demo", "mt5_live"}:
        broker = MT5Broker(config.mt5, mode=config.mode, mt5_module=mt5_module)
        broker.connect()
        market_data = MT5MarketDataProvider(broker.mt5_module)
    else:
        raise ValueError(f"unsupported mode: {config.mode}")

    return TradingEngine(
        symbols=tuple(config.symbols),
        market_data=market_data,
        strategy=TrendFollowingStrategy(config.strategy),
        risk_manager=RiskManager(config.risk),
        broker=broker,
        journal=JsonlJournal(journal_path),
        spread_points={
            symbol.name: min(config.strategy.max_spread_points, 10)
            for symbol in config.symbols
        },
    )
