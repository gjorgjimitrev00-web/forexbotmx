from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a bot config is missing required safe V1 settings."""


@dataclass(frozen=True)
class SymbolConfig:
    name: str
    point: float
    point_value_per_lot: float
    min_volume: float
    max_volume: float
    volume_step: float


@dataclass(frozen=True)
class RiskConfig:
    risk_per_trade_pct: float
    max_daily_loss_pct: float
    max_open_trades: int
    max_open_trades_per_symbol: int


@dataclass(frozen=True)
class StrategyConfig:
    fast_sma: int
    slow_sma: int
    atr_period: int
    atr_stop_multiplier: float
    take_profit_r_multiple: float
    max_spread_points: float


@dataclass(frozen=True)
class AccountConfig:
    starting_equity: float


@dataclass(frozen=True)
class MarketDataConfig:
    provider: str
    path: Path


@dataclass(frozen=True)
class BotConfig:
    mode: str
    account: AccountConfig
    risk: RiskConfig
    strategy: StrategyConfig
    market_data: MarketDataConfig
    symbols: list[SymbolConfig]


def load_config(path: Path) -> BotConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = _mapping(raw, "config")

    mode = _required(root, "mode")
    if mode == "live":
        raise ConfigError("live trading is locked for V1")
    if mode not in {"paper", "backtest", "mt5_demo"}:
        raise ConfigError("mode must be paper, backtest, or mt5_demo")

    account_raw = _mapping(_required(root, "account"), "account")
    risk_raw = _mapping(_required(root, "risk"), "risk")
    strategy_raw = _mapping(_required(root, "strategy"), "strategy")
    market_data_raw = _mapping(_required(root, "market_data"), "market_data")

    account = AccountConfig(
        starting_equity=_positive_float(account_raw, "starting_equity"),
    )

    risk = RiskConfig(
        risk_per_trade_pct=_bounded_positive_float(risk_raw, "risk_per_trade_pct", 0.25),
        max_daily_loss_pct=_bounded_positive_float(risk_raw, "max_daily_loss_pct", 1.0),
        max_open_trades=_bounded_positive_int(risk_raw, "max_open_trades", 3),
        max_open_trades_per_symbol=_bounded_positive_int(risk_raw, "max_open_trades_per_symbol", 1),
    )

    fast_sma = _positive_int(strategy_raw, "fast_sma")
    slow_sma = _positive_int(strategy_raw, "slow_sma")
    if fast_sma >= slow_sma:
        raise ConfigError("fast_sma must be less than slow_sma")

    strategy = StrategyConfig(
        fast_sma=fast_sma,
        slow_sma=slow_sma,
        atr_period=_positive_int(strategy_raw, "atr_period"),
        atr_stop_multiplier=_positive_float(strategy_raw, "atr_stop_multiplier"),
        take_profit_r_multiple=_positive_float(strategy_raw, "take_profit_r_multiple"),
        max_spread_points=_positive_float(strategy_raw, "max_spread_points"),
    )

    provider = _required(market_data_raw, "provider")
    if provider != "json":
        raise ConfigError("market_data.provider must be json in V1")

    market_data = MarketDataConfig(
        provider=provider,
        path=Path(str(_required(market_data_raw, "path"))),
    )

    symbols_raw = _required(root, "symbols")
    if not isinstance(symbols_raw, list) or not symbols_raw:
        raise ConfigError("symbols must be a non-empty list")

    return BotConfig(
        mode=mode,
        account=account,
        risk=risk,
        strategy=strategy,
        market_data=market_data,
        symbols=[_symbol_config(symbol_raw, index) for index, symbol_raw in enumerate(symbols_raw)],
    )


def _symbol_config(raw: Any, index: int) -> SymbolConfig:
    symbol = _mapping(raw, f"symbols[{index}]")
    name = _required(symbol, "name")
    if not isinstance(name, str) or not name or name != name.upper():
        raise ConfigError("symbol.name must be uppercase and non-empty")

    return SymbolConfig(
        name=name,
        point=_positive_float(symbol, "point"),
        point_value_per_lot=_positive_float(symbol, "point_value_per_lot"),
        min_volume=_positive_float(symbol, "min_volume"),
        max_volume=_positive_float(symbol, "max_volume"),
        volume_step=_positive_float(symbol, "volume_step"),
    )


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be a mapping")
    return value


def _required(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"missing required config key: {key}")
    return mapping[key]


def _positive_float(mapping: dict[str, Any], key: str) -> float:
    value = _required(mapping, key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ConfigError(f"{key} must be a positive number")
    numeric = float(value)
    if numeric <= 0:
        raise ConfigError(f"{key} must be positive")
    return numeric


def _bounded_positive_float(mapping: dict[str, Any], key: str, upper_limit: float) -> float:
    value = _positive_float(mapping, key)
    if value > upper_limit:
        raise ConfigError(f"{key} must be <= {upper_limit}")
    return value


def _positive_int(mapping: dict[str, Any], key: str) -> int:
    value = _required(mapping, key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{key} must be a positive integer")
    if value <= 0:
        raise ConfigError(f"{key} must be positive")
    return value


def _bounded_positive_int(mapping: dict[str, Any], key: str, upper_limit: int) -> int:
    value = _positive_int(mapping, key)
    if value > upper_limit:
        raise ConfigError(f"{key} must be <= {upper_limit}")
    return value
