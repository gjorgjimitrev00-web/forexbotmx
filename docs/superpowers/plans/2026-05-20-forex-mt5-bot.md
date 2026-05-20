# Forex MT5 Bot V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cautious Python forex bot that runs locally in paper/backtest mode and has a guarded Windows-only MetaTrader 5 demo adapter.

**Architecture:** The project is engine-first: strategy, risk, market data, and journaling are pure Python and do not import MT5. Broker adapters sit behind interfaces, with `PaperBroker` used locally and `MT5Broker` guarded behind a runtime import on Windows.

**Tech Stack:** Python 3.11+, `argparse`, `dataclasses`, `json`, `logging`, `PyYAML`, `pytest`, optional `MetaTrader5` extra on Windows.

---

## File Structure

- `pyproject.toml` - package metadata, dependencies, pytest configuration, optional MT5 dependency.
- `.gitignore` - ignore Python caches, virtualenvs, runtime logs, and local secrets.
- `README.md` - quickstart, safety notes, commands.
- `configs/paper.yaml` - default paper-mode config.
- `configs/backtest.yaml` - default backtest config using the same strategy/risk settings.
- `data/sample_candles.json` - deterministic sample candles for smoke tests and local paper mode.
- `docs/windows-mt5-setup.md` - Windows setup notes for MT5 demo mode.
- `src/forexbot/__init__.py` - package version.
- `src/forexbot/__main__.py` - `python -m forexbot` entrypoint.
- `src/forexbot/cli.py` - CLI commands: `check-config`, `run`, `backtest`.
- `src/forexbot/config.py` - YAML loading and V1 safety validation.
- `src/forexbot/models.py` - shared dataclasses and enums.
- `src/forexbot/indicators.py` - SMA and ATR helpers.
- `src/forexbot/market_data.py` - market data provider interfaces plus JSON sample provider.
- `src/forexbot/strategy.py` - conservative trend-following strategy.
- `src/forexbot/risk.py` - position sizing and trade approval.
- `src/forexbot/broker.py` - broker protocol and paper broker.
- `src/forexbot/mt5_broker.py` - guarded MT5 demo broker adapter.
- `src/forexbot/journal.py` - JSONL decision journal.
- `src/forexbot/engine.py` - one-cycle and loop orchestration.
- `tests/test_imports.py` - project import and CLI entrypoint smoke tests.
- `tests/test_config.py` - config validation and unsafe setting rejection.
- `tests/test_indicators.py` - indicator calculations.
- `tests/test_strategy.py` - buy/sell/hold strategy behavior.
- `tests/test_risk.py` - position sizing and risk blocking.
- `tests/test_broker.py` - paper broker behavior.
- `tests/test_engine.py` - cycle orchestration and duplicate-candle guard.
- `tests/test_mt5_broker.py` - MT5 adapter import guard and setup error.
- `tests/test_cli.py` - command-line smoke coverage.

---

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `src/forexbot/__init__.py`
- Create: `src/forexbot/__main__.py`
- Create: `src/forexbot/cli.py`
- Test: `tests/test_imports.py`

- [ ] **Step 1: Write the failing import tests**

Create `tests/test_imports.py`:

```python
import subprocess
import sys

import forexbot


def test_package_exposes_version():
    assert forexbot.__version__ == "0.1.0"


def test_module_entrypoint_shows_help():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "check-config" in result.stdout
    assert "backtest" in result.stdout
```

- [ ] **Step 2: Run the import tests to verify they fail**

Run: `pytest tests/test_imports.py -v`

Expected: FAIL because the `forexbot` package and CLI do not exist.

- [ ] **Step 3: Add project metadata and package skeleton**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "forexbot"
version = "0.1.0"
description = "Risk-controlled Python forex trading bot for paper mode and MT5 demo integration."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "PyYAML>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]
mt5 = [
    "MetaTrader5>=5.0.45",
]

[project.scripts]
forexbot = "forexbot.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
dist/
build/
*.egg-info/
logs/
journals/
.env
mt5-secrets.yaml
```

Create `src/forexbot/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/forexbot/__main__.py`:

```python
from forexbot.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `src/forexbot/cli.py`:

```python
from __future__ import annotations

import argparse


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
    print(f"{args.command} command is available; engine wiring is added in Task 8.")
    return 0
```

Create `README.md`:

```markdown
# Forexbot

Python trading bot for conservative forex paper trading and guarded MetaTrader 5 demo execution.

V1 is paper/demo focused. It does not unlock live trading.

## Commands

```bash
python -m forexbot check-config --config configs/paper.yaml
python -m forexbot run --config configs/paper.yaml --once
python -m forexbot backtest --config configs/backtest.yaml
```
```

- [ ] **Step 4: Run the import tests to verify they pass**

Run: `pytest tests/test_imports.py -v`

Expected: PASS.

- [ ] **Step 5: Commit the skeleton**

```bash
git add pyproject.toml .gitignore README.md src/forexbot/__init__.py src/forexbot/__main__.py src/forexbot/cli.py tests/test_imports.py
git commit -m "chore: add forexbot project skeleton"
```

---

## Task 2: Config Loading And Safety Validation

**Files:**
- Create: `configs/paper.yaml`
- Create: `configs/backtest.yaml`
- Create: `src/forexbot/config.py`
- Modify: `src/forexbot/cli.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

import pytest

from forexbot.config import ConfigError, load_config


def test_loads_paper_config():
    config = load_config(Path("configs/paper.yaml"))

    assert config.mode == "paper"
    assert config.risk.risk_per_trade_pct == 0.25
    assert config.risk.max_daily_loss_pct == 1.0
    assert [symbol.name for symbol in config.symbols] == ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]


def test_rejects_live_mode(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
mode: live
account:
  starting_equity: 10000
risk:
  risk_per_trade_pct: 0.25
  max_daily_loss_pct: 1.0
  max_open_trades: 3
  max_open_trades_per_symbol: 1
strategy:
  fast_sma: 20
  slow_sma: 50
  atr_period: 14
  atr_stop_multiplier: 1.5
  take_profit_r_multiple: 2.0
  max_spread_points: 25
market_data:
  provider: json
  path: data/sample_candles.json
symbols: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="live trading is locked"):
        load_config(path)


def test_rejects_risk_above_v1_limit(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
mode: paper
account:
  starting_equity: 10000
risk:
  risk_per_trade_pct: 0.5
  max_daily_loss_pct: 1.0
  max_open_trades: 3
  max_open_trades_per_symbol: 1
strategy:
  fast_sma: 20
  slow_sma: 50
  atr_period: 14
  atr_stop_multiplier: 1.5
  take_profit_r_multiple: 2.0
  max_spread_points: 25
market_data:
  provider: json
  path: data/sample_candles.json
symbols:
  - name: EURUSD
    point: 0.0001
    point_value_per_lot: 10
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="risk_per_trade_pct"):
        load_config(path)
```

- [ ] **Step 2: Run config tests to verify they fail**

Run: `pytest tests/test_config.py -v`

Expected: FAIL because `forexbot.config` and config files do not exist.

- [ ] **Step 3: Add config dataclasses and validation**

Create `src/forexbot/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    pass


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
    symbols: tuple[SymbolConfig, ...]


def load_config(path: Path) -> BotConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")

    mode = str(raw.get("mode", "")).strip()
    if mode == "live":
        raise ConfigError("live trading is locked in V1")
    if mode not in {"paper", "backtest", "mt5_demo"}:
        raise ConfigError("mode must be paper, backtest, or mt5_demo")

    account = _account(raw.get("account"))
    risk = _risk(raw.get("risk"))
    strategy = _strategy(raw.get("strategy"))
    market_data = _market_data(raw.get("market_data"))
    symbols = tuple(_symbol(item) for item in _required_list(raw, "symbols"))

    if not symbols:
        raise ConfigError("at least one symbol is required")

    return BotConfig(
        mode=mode,
        account=account,
        risk=risk,
        strategy=strategy,
        market_data=market_data,
        symbols=symbols,
    )


def _account(raw: Any) -> AccountConfig:
    data = _required_mapping(raw, "account")
    starting_equity = _positive_float(data, "starting_equity")
    return AccountConfig(starting_equity=starting_equity)


def _risk(raw: Any) -> RiskConfig:
    data = _required_mapping(raw, "risk")
    risk_per_trade_pct = _positive_float(data, "risk_per_trade_pct")
    max_daily_loss_pct = _positive_float(data, "max_daily_loss_pct")
    max_open_trades = _positive_int(data, "max_open_trades")
    max_open_trades_per_symbol = _positive_int(data, "max_open_trades_per_symbol")

    if risk_per_trade_pct > 0.25:
        raise ConfigError("risk_per_trade_pct must be <= 0.25 for V1")
    if max_daily_loss_pct > 1.0:
        raise ConfigError("max_daily_loss_pct must be <= 1.0 for V1")
    if max_open_trades > 3:
        raise ConfigError("max_open_trades must be <= 3 for V1")
    if max_open_trades_per_symbol > 1:
        raise ConfigError("max_open_trades_per_symbol must be <= 1 for V1")

    return RiskConfig(
        risk_per_trade_pct=risk_per_trade_pct,
        max_daily_loss_pct=max_daily_loss_pct,
        max_open_trades=max_open_trades,
        max_open_trades_per_symbol=max_open_trades_per_symbol,
    )


def _strategy(raw: Any) -> StrategyConfig:
    data = _required_mapping(raw, "strategy")
    fast_sma = _positive_int(data, "fast_sma")
    slow_sma = _positive_int(data, "slow_sma")
    if fast_sma >= slow_sma:
        raise ConfigError("fast_sma must be lower than slow_sma")

    return StrategyConfig(
        fast_sma=fast_sma,
        slow_sma=slow_sma,
        atr_period=_positive_int(data, "atr_period"),
        atr_stop_multiplier=_positive_float(data, "atr_stop_multiplier"),
        take_profit_r_multiple=_positive_float(data, "take_profit_r_multiple"),
        max_spread_points=_positive_float(data, "max_spread_points"),
    )


def _market_data(raw: Any) -> MarketDataConfig:
    data = _required_mapping(raw, "market_data")
    provider = str(data.get("provider", "")).strip()
    if provider != "json":
        raise ConfigError("market_data.provider must be json in V1")
    return MarketDataConfig(provider=provider, path=Path(str(data.get("path", ""))))


def _symbol(raw: Any) -> SymbolConfig:
    data = _required_mapping(raw, "symbol")
    name = str(data.get("name", "")).strip().upper()
    if not name:
        raise ConfigError("symbol.name is required")
    return SymbolConfig(
        name=name,
        point=_positive_float(data, "point"),
        point_value_per_lot=_positive_float(data, "point_value_per_lot"),
        min_volume=_positive_float(data, "min_volume"),
        max_volume=_positive_float(data, "max_volume"),
        volume_step=_positive_float(data, "volume_step"),
    )


def _required_mapping(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ConfigError(f"{name} must be a mapping")
    return raw


def _required_list(raw: dict[str, Any], key: str) -> list[Any]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ConfigError(f"{key} must be a list")
    return value


def _positive_float(data: dict[str, Any], key: str) -> float:
    value = float(data[key])
    if value <= 0:
        raise ConfigError(f"{key} must be positive")
    return value


def _positive_int(data: dict[str, Any], key: str) -> int:
    value = int(data[key])
    if value <= 0:
        raise ConfigError(f"{key} must be positive")
    return value
```

- [ ] **Step 4: Add default configs**

Create `configs/paper.yaml`:

```yaml
mode: paper
account:
  starting_equity: 10000
risk:
  risk_per_trade_pct: 0.25
  max_daily_loss_pct: 1.0
  max_open_trades: 3
  max_open_trades_per_symbol: 1
strategy:
  fast_sma: 20
  slow_sma: 50
  atr_period: 14
  atr_stop_multiplier: 1.5
  take_profit_r_multiple: 2.0
  max_spread_points: 25
market_data:
  provider: json
  path: data/sample_candles.json
symbols:
  - name: EURUSD
    point: 0.0001
    point_value_per_lot: 10
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
  - name: GBPUSD
    point: 0.0001
    point_value_per_lot: 10
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
  - name: USDJPY
    point: 0.01
    point_value_per_lot: 9
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
  - name: XAUUSD
    point: 0.01
    point_value_per_lot: 1
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
```

Create `configs/backtest.yaml`:

```yaml
mode: backtest
account:
  starting_equity: 10000
risk:
  risk_per_trade_pct: 0.25
  max_daily_loss_pct: 1.0
  max_open_trades: 3
  max_open_trades_per_symbol: 1
strategy:
  fast_sma: 20
  slow_sma: 50
  atr_period: 14
  atr_stop_multiplier: 1.5
  take_profit_r_multiple: 2.0
  max_spread_points: 25
market_data:
  provider: json
  path: data/sample_candles.json
symbols:
  - name: EURUSD
    point: 0.0001
    point_value_per_lot: 10
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
  - name: GBPUSD
    point: 0.0001
    point_value_per_lot: 10
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
  - name: USDJPY
    point: 0.01
    point_value_per_lot: 9
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
  - name: XAUUSD
    point: 0.01
    point_value_per_lot: 1
    min_volume: 0.01
    max_volume: 1.0
    volume_step: 0.01
```

- [ ] **Step 5: Wire `check-config`**

Replace `src/forexbot/cli.py` with:

```python
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
        parser.exit(status=2, message=f"config error: {exc}\n")

    if args.command == "check-config":
        print(f"OK: {args.config} mode={config.mode} symbols={len(config.symbols)}")
        return 0

    print(f"{args.command} command is available for mode={config.mode}; engine wiring is added in Task 8.")
    return 0
```

- [ ] **Step 6: Run config tests and CLI smoke**

Run: `pytest tests/test_config.py -v`

Expected: PASS.

Run: `python -m forexbot check-config --config configs/paper.yaml`

Expected: `OK: configs/paper.yaml mode=paper symbols=4`

- [ ] **Step 7: Commit config work**

```bash
git add configs/paper.yaml configs/backtest.yaml src/forexbot/config.py src/forexbot/cli.py tests/test_config.py
git commit -m "feat: add safe bot config loading"
```

---

## Task 3: Models And Indicators

**Files:**
- Create: `src/forexbot/models.py`
- Create: `src/forexbot/indicators.py`
- Test: `tests/test_indicators.py`

- [ ] **Step 1: Write failing indicator tests**

Create `tests/test_indicators.py`:

```python
from datetime import datetime, timezone

from forexbot.indicators import atr, sma
from forexbot.models import Candle


def candle(high: float, low: float, close: float) -> Candle:
    return Candle(
        symbol="EURUSD",
        timeframe="M15",
        time=datetime(2026, 5, 20, tzinfo=timezone.utc),
        open=close,
        high=high,
        low=low,
        close=close,
        volume=1000,
    )


def test_sma_uses_last_period_values():
    assert sma([1, 2, 3, 4, 5], 3) == 4


def test_sma_returns_none_without_enough_values():
    assert sma([1, 2], 3) is None


def test_atr_uses_true_range_average():
    candles = [
        candle(1.1050, 1.1000, 1.1020),
        candle(1.1080, 1.1010, 1.1070),
        candle(1.1090, 1.1040, 1.1050),
    ]

    assert atr(candles, 2) == 0.006
```

- [ ] **Step 2: Run indicator tests to verify they fail**

Run: `pytest tests/test_indicators.py -v`

Expected: FAIL because models and indicators do not exist.

- [ ] **Step 3: Add shared models**

Create `src/forexbot/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side
    reason: str
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    candle_time: datetime | None = None


@dataclass(frozen=True)
class TradeIntent:
    symbol: str
    side: Side
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    candle_time: datetime


@dataclass(frozen=True)
class Position:
    symbol: str
    side: Side
    volume: float
    entry_price: float
    stop_loss: float
    opened_at: datetime


@dataclass(frozen=True)
class AccountState:
    equity: float
    balance: float
    daily_realized_pnl: float
    open_positions: tuple[Position, ...] = ()


@dataclass(frozen=True)
class OrderResult:
    accepted: bool
    order_id: str | None
    message: str
```

- [ ] **Step 4: Add indicator helpers**

Create `src/forexbot/indicators.py`:

```python
from __future__ import annotations

from forexbot.models import Candle


def sma(values: list[float], period: int) -> float | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def atr(candles: list[Candle], period: int) -> float | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period + 1:
        return None

    ranges: list[float] = []
    recent = candles[-period:]
    previous = candles[-period - 1 : -1]
    for current, prior in zip(recent, previous):
        ranges.append(
            max(
                current.high - current.low,
                abs(current.high - prior.close),
                abs(current.low - prior.close),
            )
        )

    return round(sum(ranges) / period, 10)
```

- [ ] **Step 5: Run indicator tests**

Run: `pytest tests/test_indicators.py -v`

Expected: PASS.

- [ ] **Step 6: Commit models and indicators**

```bash
git add src/forexbot/models.py src/forexbot/indicators.py tests/test_indicators.py
git commit -m "feat: add trading models and indicators"
```

---

## Task 4: Conservative Trend Strategy

**Files:**
- Create: `src/forexbot/strategy.py`
- Test: `tests/test_strategy.py`

- [ ] **Step 1: Write failing strategy tests**

Create `tests/test_strategy.py`:

```python
from datetime import datetime, timedelta, timezone

from forexbot.config import StrategyConfig, SymbolConfig
from forexbot.models import Candle, Side
from forexbot.strategy import TrendFollowingStrategy


def make_candles(symbol: str, timeframe: str, start: float, step: float, count: int) -> list[Candle]:
    base = datetime(2026, 5, 20, tzinfo=timezone.utc)
    candles: list[Candle] = []
    for index in range(count):
        close = start + (step * index)
        candles.append(
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                time=base + timedelta(minutes=15 * index),
                open=close - (step / 2),
                high=close + 0.0010,
                low=close - 0.0010,
                close=close,
                volume=1000,
            )
        )
    return candles


def config() -> StrategyConfig:
    return StrategyConfig(
        fast_sma=3,
        slow_sma=5,
        atr_period=3,
        atr_stop_multiplier=1.5,
        take_profit_r_multiple=2.0,
        max_spread_points=20,
    )


def symbol() -> SymbolConfig:
    return SymbolConfig(
        name="EURUSD",
        point=0.0001,
        point_value_per_lot=10,
        min_volume=0.01,
        max_volume=1,
        volume_step=0.01,
    )


def test_returns_buy_when_m15_and_h1_trend_up():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=10)

    assert signal.side == Side.BUY
    assert signal.entry_price == m15[-1].close
    assert signal.stop_loss < signal.entry_price
    assert signal.take_profit > signal.entry_price


def test_returns_sell_when_m15_and_h1_trend_down():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1200, -0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.1400, -0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=10)

    assert signal.side == Side.SELL
    assert signal.stop_loss > signal.entry_price
    assert signal.take_profit < signal.entry_price


def test_holds_when_spread_is_too_high():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=25)

    assert signal.side == Side.HOLD
    assert "spread" in signal.reason
```

- [ ] **Step 2: Run strategy tests to verify they fail**

Run: `pytest tests/test_strategy.py -v`

Expected: FAIL because `TrendFollowingStrategy` does not exist.

- [ ] **Step 3: Implement the strategy**

Create `src/forexbot/strategy.py`:

```python
from __future__ import annotations

from forexbot.config import StrategyConfig, SymbolConfig
from forexbot.indicators import atr, sma
from forexbot.models import Candle, Side, Signal


class TrendFollowingStrategy:
    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    def evaluate(
        self,
        symbol: SymbolConfig,
        *,
        m15: list[Candle],
        h1: list[Candle],
        spread_points: float,
    ) -> Signal:
        if spread_points > self.config.max_spread_points:
            return Signal(symbol=symbol.name, side=Side.HOLD, reason="spread above configured maximum")

        min_candles = max(self.config.slow_sma, self.config.atr_period + 1)
        if len(m15) < min_candles or len(h1) < self.config.slow_sma:
            return Signal(symbol=symbol.name, side=Side.HOLD, reason="not enough candle history")

        m15_closes = [candle.close for candle in m15]
        h1_closes = [candle.close for candle in h1]

        m15_fast = sma(m15_closes, self.config.fast_sma)
        m15_slow = sma(m15_closes, self.config.slow_sma)
        h1_fast = sma(h1_closes, self.config.fast_sma)
        h1_slow = sma(h1_closes, self.config.slow_sma)
        volatility = atr(m15, self.config.atr_period)

        if None in {m15_fast, m15_slow, h1_fast, h1_slow, volatility}:
            return Signal(symbol=symbol.name, side=Side.HOLD, reason="indicator warmup")
        if volatility <= 0:
            return Signal(symbol=symbol.name, side=Side.HOLD, reason="volatility is zero")

        latest = m15[-1]
        prior = m15[-2]

        trend_up = m15_fast > m15_slow and h1_fast > h1_slow and latest.close > prior.close
        trend_down = m15_fast < m15_slow and h1_fast < h1_slow and latest.close < prior.close
        stop_distance = volatility * self.config.atr_stop_multiplier

        if trend_up:
            return Signal(
                symbol=symbol.name,
                side=Side.BUY,
                reason="M15 and H1 trend up",
                entry_price=latest.close,
                stop_loss=latest.close - stop_distance,
                take_profit=latest.close + (stop_distance * self.config.take_profit_r_multiple),
                candle_time=latest.time,
            )

        if trend_down:
            return Signal(
                symbol=symbol.name,
                side=Side.SELL,
                reason="M15 and H1 trend down",
                entry_price=latest.close,
                stop_loss=latest.close + stop_distance,
                take_profit=latest.close - (stop_distance * self.config.take_profit_r_multiple),
                candle_time=latest.time,
            )

        return Signal(symbol=symbol.name, side=Side.HOLD, reason="trend confirmation failed", candle_time=latest.time)
```

- [ ] **Step 4: Run strategy tests**

Run: `pytest tests/test_strategy.py -v`

Expected: PASS.

- [ ] **Step 5: Commit strategy**

```bash
git add src/forexbot/strategy.py tests/test_strategy.py
git commit -m "feat: add conservative trend strategy"
```

---

## Task 5: Risk Manager And Position Sizing

**Files:**
- Create: `src/forexbot/risk.py`
- Test: `tests/test_risk.py`

- [ ] **Step 1: Write failing risk tests**

Create `tests/test_risk.py`:

```python
from datetime import datetime, timezone

from forexbot.config import RiskConfig, SymbolConfig
from forexbot.models import AccountState, Position, Side, Signal
from forexbot.risk import RiskManager


def risk() -> RiskConfig:
    return RiskConfig(
        risk_per_trade_pct=0.25,
        max_daily_loss_pct=1.0,
        max_open_trades=3,
        max_open_trades_per_symbol=1,
    )


def symbol() -> SymbolConfig:
    return SymbolConfig(
        name="EURUSD",
        point=0.0001,
        point_value_per_lot=10,
        min_volume=0.01,
        max_volume=1,
        volume_step=0.01,
    )


def buy_signal() -> Signal:
    return Signal(
        symbol="EURUSD",
        side=Side.BUY,
        reason="test",
        entry_price=1.1050,
        stop_loss=1.1000,
        take_profit=1.1150,
        candle_time=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )


def test_sizes_position_from_risk_and_stop_distance():
    manager = RiskManager(risk())
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=0)

    decision = manager.evaluate(symbol(), account, buy_signal())

    assert decision.allowed is True
    assert decision.intent is not None
    assert decision.intent.volume == 0.05


def test_blocks_when_daily_loss_limit_reached():
    manager = RiskManager(risk())
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=-100)

    decision = manager.evaluate(symbol(), account, buy_signal())

    assert decision.allowed is False
    assert "daily loss" in decision.reason


def test_blocks_when_symbol_already_has_open_position():
    manager = RiskManager(risk())
    position = Position(
        symbol="EURUSD",
        side=Side.BUY,
        volume=0.01,
        entry_price=1.1000,
        stop_loss=1.0950,
        opened_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=0, open_positions=(position,))

    decision = manager.evaluate(symbol(), account, buy_signal())

    assert decision.allowed is False
    assert "per-symbol" in decision.reason
```

- [ ] **Step 2: Run risk tests to verify they fail**

Run: `pytest tests/test_risk.py -v`

Expected: FAIL because `RiskManager` does not exist.

- [ ] **Step 3: Implement risk manager**

Create `src/forexbot/risk.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from forexbot.config import RiskConfig, SymbolConfig
from forexbot.models import AccountState, Side, Signal, TradeIntent


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    intent: TradeIntent | None = None


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def evaluate(self, symbol: SymbolConfig, account: AccountState, signal: Signal) -> RiskDecision:
        if signal.side == Side.HOLD:
            return RiskDecision(False, signal.reason)
        if signal.entry_price is None or signal.stop_loss is None or signal.take_profit is None or signal.candle_time is None:
            return RiskDecision(False, "signal is missing required order prices")
        if len(account.open_positions) >= self.config.max_open_trades:
            return RiskDecision(False, "max open trades reached")

        symbol_positions = [position for position in account.open_positions if position.symbol == symbol.name]
        if len(symbol_positions) >= self.config.max_open_trades_per_symbol:
            return RiskDecision(False, "per-symbol open trade limit reached")

        daily_loss_limit = account.equity * (self.config.max_daily_loss_pct / 100)
        if account.daily_realized_pnl <= -daily_loss_limit:
            return RiskDecision(False, "daily loss limit reached")

        volume = self._position_size(symbol, account.equity, signal.entry_price, signal.stop_loss)
        if volume < symbol.min_volume:
            return RiskDecision(False, "calculated volume below minimum")

        return RiskDecision(
            True,
            "risk checks passed",
            TradeIntent(
                symbol=symbol.name,
                side=signal.side,
                volume=volume,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                reason=signal.reason,
                candle_time=signal.candle_time,
            ),
        )

    def _position_size(self, symbol: SymbolConfig, equity: float, entry: float, stop: float) -> float:
        stop_points = abs(entry - stop) / symbol.point
        if stop_points <= 0:
            return 0.0

        risk_amount = equity * (self.config.risk_per_trade_pct / 100)
        raw_volume = risk_amount / (stop_points * symbol.point_value_per_lot)
        bounded = min(max(raw_volume, symbol.min_volume), symbol.max_volume)

        step = Decimal(str(symbol.volume_step))
        value = Decimal(str(bounded))
        rounded = (value / step).to_integral_value(rounding=ROUND_DOWN) * step
        return float(rounded)
```

- [ ] **Step 4: Run risk tests**

Run: `pytest tests/test_risk.py -v`

Expected: PASS.

- [ ] **Step 5: Commit risk manager**

```bash
git add src/forexbot/risk.py tests/test_risk.py
git commit -m "feat: add risk manager"
```

---

## Task 6: Market Data Provider And Paper Broker

**Files:**
- Create: `data/sample_candles.json`
- Create: `src/forexbot/market_data.py`
- Create: `src/forexbot/broker.py`
- Test: `tests/test_broker.py`

- [ ] **Step 1: Write failing broker and market data tests**

Create `tests/test_broker.py`:

```python
from datetime import datetime, timezone

from forexbot.broker import PaperBroker
from forexbot.market_data import JsonMarketDataProvider
from forexbot.models import AccountState, Side, TradeIntent


def intent() -> TradeIntent:
    return TradeIntent(
        symbol="EURUSD",
        side=Side.BUY,
        volume=0.05,
        entry_price=1.1050,
        stop_loss=1.1000,
        take_profit=1.1150,
        reason="test",
        candle_time=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )


def test_paper_broker_records_order():
    broker = PaperBroker(starting_equity=10000)

    result = broker.place_order(intent())

    assert result.accepted is True
    assert result.order_id == "paper-1"
    assert len(broker.orders) == 1


def test_paper_broker_exposes_account_state():
    broker = PaperBroker(starting_equity=10000)

    state = broker.account_state()

    assert isinstance(state, AccountState)
    assert state.equity == 10000


def test_json_market_data_provider_loads_symbol_timeframe():
    provider = JsonMarketDataProvider("data/sample_candles.json")

    candles = provider.recent_candles("EURUSD", "M15", limit=10)

    assert len(candles) == 10
    assert candles[-1].symbol == "EURUSD"
    assert candles[-1].time.tzinfo is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_broker.py -v`

Expected: FAIL because broker, market data, and sample candles do not exist.

- [ ] **Step 3: Add sample market data**

Create `data/sample_candles.json` with enough rising candle history for each configured symbol and both timeframes:

```json
{
  "EURUSD": {
    "M15": [
      {"time": "2026-05-20T06:00:00+00:00", "open": 1.1000, "high": 1.1012, "low": 1.0992, "close": 1.1005, "volume": 1000},
      {"time": "2026-05-20T06:15:00+00:00", "open": 1.1005, "high": 1.1017, "low": 1.0997, "close": 1.1010, "volume": 1000},
      {"time": "2026-05-20T06:30:00+00:00", "open": 1.1010, "high": 1.1022, "low": 1.1002, "close": 1.1015, "volume": 1000},
      {"time": "2026-05-20T06:45:00+00:00", "open": 1.1015, "high": 1.1027, "low": 1.1007, "close": 1.1020, "volume": 1000},
      {"time": "2026-05-20T07:00:00+00:00", "open": 1.1020, "high": 1.1032, "low": 1.1012, "close": 1.1025, "volume": 1000},
      {"time": "2026-05-20T07:15:00+00:00", "open": 1.1025, "high": 1.1037, "low": 1.1017, "close": 1.1030, "volume": 1000},
      {"time": "2026-05-20T07:30:00+00:00", "open": 1.1030, "high": 1.1042, "low": 1.1022, "close": 1.1035, "volume": 1000},
      {"time": "2026-05-20T07:45:00+00:00", "open": 1.1035, "high": 1.1047, "low": 1.1027, "close": 1.1040, "volume": 1000},
      {"time": "2026-05-20T08:00:00+00:00", "open": 1.1040, "high": 1.1052, "low": 1.1032, "close": 1.1045, "volume": 1000},
      {"time": "2026-05-20T08:15:00+00:00", "open": 1.1045, "high": 1.1057, "low": 1.1037, "close": 1.1050, "volume": 1000}
    ],
    "H1": [
      {"time": "2026-05-20T00:00:00+00:00", "open": 1.0900, "high": 1.0920, "low": 1.0890, "close": 1.0910, "volume": 2000},
      {"time": "2026-05-20T01:00:00+00:00", "open": 1.0910, "high": 1.0930, "low": 1.0900, "close": 1.0920, "volume": 2000},
      {"time": "2026-05-20T02:00:00+00:00", "open": 1.0920, "high": 1.0940, "low": 1.0910, "close": 1.0930, "volume": 2000},
      {"time": "2026-05-20T03:00:00+00:00", "open": 1.0930, "high": 1.0950, "low": 1.0920, "close": 1.0940, "volume": 2000},
      {"time": "2026-05-20T04:00:00+00:00", "open": 1.0940, "high": 1.0960, "low": 1.0930, "close": 1.0950, "volume": 2000},
      {"time": "2026-05-20T05:00:00+00:00", "open": 1.0950, "high": 1.0970, "low": 1.0940, "close": 1.0960, "volume": 2000},
      {"time": "2026-05-20T06:00:00+00:00", "open": 1.0960, "high": 1.0980, "low": 1.0950, "close": 1.0970, "volume": 2000},
      {"time": "2026-05-20T07:00:00+00:00", "open": 1.0970, "high": 1.0990, "low": 1.0960, "close": 1.0980, "volume": 2000},
      {"time": "2026-05-20T08:00:00+00:00", "open": 1.0980, "high": 1.1000, "low": 1.0970, "close": 1.0990, "volume": 2000},
      {"time": "2026-05-20T09:00:00+00:00", "open": 1.0990, "high": 1.1010, "low": 1.0980, "close": 1.1000, "volume": 2000}
    ]
  }
}
```

- [ ] **Step 4: Implement market data provider**

Create `src/forexbot/market_data.py`:

```python
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

from forexbot.models import Candle


class MarketDataProvider(Protocol):
    def recent_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        ...


class JsonMarketDataProvider:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._raw = json.loads(self.path.read_text(encoding="utf-8"))

    def recent_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        rows = self._raw[symbol][timeframe][-limit:]
        return [
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                time=datetime.fromisoformat(row["time"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for row in rows
        ]
```

- [ ] **Step 5: Implement paper broker**

Create `src/forexbot/broker.py`:

```python
from __future__ import annotations

from typing import Protocol

from forexbot.models import AccountState, OrderResult, TradeIntent


class Broker(Protocol):
    def account_state(self) -> AccountState:
        ...

    def place_order(self, intent: TradeIntent) -> OrderResult:
        ...


class PaperBroker:
    def __init__(self, starting_equity: float) -> None:
        self.starting_equity = starting_equity
        self.orders: list[TradeIntent] = []

    def account_state(self) -> AccountState:
        return AccountState(
            equity=self.starting_equity,
            balance=self.starting_equity,
            daily_realized_pnl=0,
        )

    def place_order(self, intent: TradeIntent) -> OrderResult:
        if intent.volume <= 0:
            return OrderResult(False, None, "volume must be positive")
        self.orders.append(intent)
        return OrderResult(True, f"paper-{len(self.orders)}", "paper order accepted")
```

- [ ] **Step 6: Run broker tests**

Run: `pytest tests/test_broker.py -v`

Expected: PASS.

- [ ] **Step 7: Commit broker and market data**

```bash
git add data/sample_candles.json src/forexbot/market_data.py src/forexbot/broker.py tests/test_broker.py
git commit -m "feat: add paper broker and sample market data"
```

---

## Task 7: Journal And Engine Cycle

**Files:**
- Create: `src/forexbot/journal.py`
- Create: `src/forexbot/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write failing engine tests**

Create `tests/test_engine.py`:

```python
import json

from forexbot.broker import PaperBroker
from forexbot.config import RiskConfig, StrategyConfig, SymbolConfig
from forexbot.engine import TradingEngine
from forexbot.journal import JsonlJournal
from forexbot.market_data import JsonMarketDataProvider
from forexbot.risk import RiskManager
from forexbot.strategy import TrendFollowingStrategy


def test_engine_runs_one_cycle_and_journals_result(tmp_path):
    journal_path = tmp_path / "journal.jsonl"
    symbol = SymbolConfig("EURUSD", 0.0001, 10, 0.01, 1.0, 0.01)
    strategy = TrendFollowingStrategy(
        StrategyConfig(
            fast_sma=3,
            slow_sma=5,
            atr_period=3,
            atr_stop_multiplier=1.5,
            take_profit_r_multiple=2.0,
            max_spread_points=20,
        )
    )
    engine = TradingEngine(
        symbols=(symbol,),
        market_data=JsonMarketDataProvider("data/sample_candles.json"),
        strategy=strategy,
        risk_manager=RiskManager(RiskConfig(0.25, 1.0, 3, 1)),
        broker=PaperBroker(starting_equity=10000),
        journal=JsonlJournal(journal_path),
        spread_points={"EURUSD": 10},
    )

    summary = engine.run_once()

    assert summary["executed"] == 1
    entries = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()]
    assert entries[-1]["event"] == "order_executed"


def test_engine_skips_duplicate_candle(tmp_path):
    journal_path = tmp_path / "journal.jsonl"
    symbol = SymbolConfig("EURUSD", 0.0001, 10, 0.01, 1.0, 0.01)
    strategy = TrendFollowingStrategy(
        StrategyConfig(3, 5, 3, 1.5, 2.0, 20)
    )
    broker = PaperBroker(starting_equity=10000)
    engine = TradingEngine(
        symbols=(symbol,),
        market_data=JsonMarketDataProvider("data/sample_candles.json"),
        strategy=strategy,
        risk_manager=RiskManager(RiskConfig(0.25, 1.0, 3, 1)),
        broker=broker,
        journal=JsonlJournal(journal_path),
        spread_points={"EURUSD": 10},
    )

    first = engine.run_once()
    second = engine.run_once()

    assert first["executed"] == 1
    assert second["duplicates"] == 1
    assert len(broker.orders) == 1
```

- [ ] **Step 2: Run engine tests to verify they fail**

Run: `pytest tests/test_engine.py -v`

Expected: FAIL because journal and engine do not exist.

- [ ] **Step 3: Implement JSONL journal**

Create `src/forexbot/journal.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JsonlJournal:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, **fields: Any) -> None:
        payload = {
            "event": event,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str, sort_keys=True) + "\n")
```

- [ ] **Step 4: Implement one-cycle engine**

Create `src/forexbot/engine.py`:

```python
from __future__ import annotations

from forexbot.broker import Broker
from forexbot.config import SymbolConfig
from forexbot.journal import JsonlJournal
from forexbot.market_data import MarketDataProvider
from forexbot.risk import RiskManager
from forexbot.strategy import TrendFollowingStrategy


class TradingEngine:
    def __init__(
        self,
        *,
        symbols: tuple[SymbolConfig, ...],
        market_data: MarketDataProvider,
        strategy: TrendFollowingStrategy,
        risk_manager: RiskManager,
        broker: Broker,
        journal: JsonlJournal,
        spread_points: dict[str, float],
    ) -> None:
        self.symbols = symbols
        self.market_data = market_data
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.broker = broker
        self.journal = journal
        self.spread_points = spread_points
        self._processed_candles: set[tuple[str, str]] = set()

    def run_once(self) -> dict[str, int]:
        summary = {"executed": 0, "blocked": 0, "held": 0, "duplicates": 0, "errors": 0}

        for symbol in self.symbols:
            try:
                m15 = self.market_data.recent_candles(symbol.name, "M15", limit=100)
                h1 = self.market_data.recent_candles(symbol.name, "H1", limit=100)
                candle_key = (symbol.name, m15[-1].time.isoformat())
                if candle_key in self._processed_candles:
                    summary["duplicates"] += 1
                    self.journal.record("duplicate_candle_skipped", symbol=symbol.name, candle_time=m15[-1].time)
                    continue
                self._processed_candles.add(candle_key)

                signal = self.strategy.evaluate(
                    symbol,
                    m15=m15,
                    h1=h1,
                    spread_points=self.spread_points.get(symbol.name, 0),
                )
                self.journal.record("signal", symbol=symbol.name, side=signal.side.value, reason=signal.reason)

                account = self.broker.account_state()
                decision = self.risk_manager.evaluate(symbol, account, signal)
                if not decision.allowed:
                    key = "held" if signal.side.value == "hold" else "blocked"
                    summary[key] += 1
                    self.journal.record("trade_blocked", symbol=symbol.name, reason=decision.reason)
                    continue

                result = self.broker.place_order(decision.intent)
                if result.accepted:
                    summary["executed"] += 1
                    self.journal.record(
                        "order_executed",
                        symbol=symbol.name,
                        order_id=result.order_id,
                        volume=decision.intent.volume,
                    )
                else:
                    summary["blocked"] += 1
                    self.journal.record("order_rejected", symbol=symbol.name, message=result.message)
            except Exception as exc:
                summary["errors"] += 1
                self.journal.record("symbol_error", symbol=symbol.name, error=str(exc))

        return summary
```

- [ ] **Step 5: Run engine tests**

Run: `pytest tests/test_engine.py -v`

Expected: PASS.

- [ ] **Step 6: Commit engine and journal**

```bash
git add src/forexbot/journal.py src/forexbot/engine.py tests/test_engine.py
git commit -m "feat: add trading engine cycle"
```

---

## Task 8: CLI Run And Backtest Smoke

**Files:**
- Modify: `src/forexbot/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
import subprocess
import sys


def test_check_config_command_succeeds():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "check-config", "--config", "configs/paper.yaml"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "mode=paper" in result.stdout


def test_run_once_command_succeeds():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "run", "--config", "configs/paper.yaml", "--once"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "executed" in result.stdout


def test_backtest_command_succeeds():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "backtest", "--config", "configs/backtest.yaml"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "backtest summary" in result.stdout
```

- [ ] **Step 2: Run CLI tests to verify run/backtest fail**

Run: `pytest tests/test_cli.py -v`

Expected: FAIL because CLI still uses stub run/backtest output.

- [ ] **Step 3: Wire CLI to engine**

Replace `src/forexbot/cli.py` with:

```python
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
        parser.exit(status=2, message=f"config error: {exc}\n")

    if args.command == "check-config":
        print(f"OK: {args.config} mode={config.mode} symbols={len(config.symbols)}")
        return 0

    if args.command == "run":
        if not args.once:
            parser.exit(status=2, message="run requires --once in V1\n")
        summary = _build_engine(config, "journals/paper.jsonl").run_once()
        print(f"paper summary: {summary}")
        return 0

    if args.command == "backtest":
        summary = _build_engine(config, "journals/backtest.jsonl").run_once()
        print(f"backtest summary: {summary}")
        return 0

    parser.exit(status=2, message="unknown command\n")
    return 2


def _build_engine(config: BotConfig, journal_path: str) -> TradingEngine:
    return TradingEngine(
        symbols=config.symbols,
        market_data=JsonMarketDataProvider(config.market_data.path),
        strategy=TrendFollowingStrategy(config.strategy),
        risk_manager=RiskManager(config.risk),
        broker=PaperBroker(config.account.starting_equity),
        journal=JsonlJournal(journal_path),
        spread_points={symbol.name: min(config.strategy.max_spread_points, 10) for symbol in config.symbols},
    )
```

- [ ] **Step 4: Run CLI tests**

Run: `pytest tests/test_cli.py -v`

Expected: PASS.

- [ ] **Step 5: Run full local smoke**

Run: `python -m forexbot run --config configs/paper.yaml --once`

Expected: command exits with code `0` and prints a summary dictionary containing `executed`.

Run: `python -m forexbot backtest --config configs/backtest.yaml`

Expected: command exits with code `0` and prints `backtest summary`.

- [ ] **Step 6: Commit CLI engine wiring**

```bash
git add src/forexbot/cli.py tests/test_cli.py
git commit -m "feat: wire CLI to paper engine"
```

---

## Task 9: Guarded MT5 Demo Adapter And Windows Notes

**Files:**
- Create: `src/forexbot/mt5_broker.py`
- Create: `docs/windows-mt5-setup.md`
- Test: `tests/test_mt5_broker.py`

- [ ] **Step 1: Write failing MT5 adapter tests**

Create `tests/test_mt5_broker.py`:

```python
import builtins

import pytest

from forexbot.mt5_broker import MT5Broker, MT5SetupError


def test_importing_mt5_broker_does_not_import_metatrader5():
    broker = MT5Broker()

    assert broker.connected is False


def test_connect_explains_missing_metatrader5(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "MetaTrader5":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    broker = MT5Broker()

    with pytest.raises(MT5SetupError, match="Windows"):
        broker.connect()
```

- [ ] **Step 2: Run MT5 tests to verify they fail**

Run: `pytest tests/test_mt5_broker.py -v`

Expected: FAIL because the MT5 adapter does not exist.

- [ ] **Step 3: Implement guarded MT5 adapter**

Create `src/forexbot/mt5_broker.py`:

```python
from __future__ import annotations

from typing import Any

from forexbot.models import AccountState, OrderResult, TradeIntent


class MT5SetupError(RuntimeError):
    pass


class MT5Broker:
    def __init__(self) -> None:
        self.connected = False
        self._mt5: Any | None = None

    def connect(self) -> None:
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise MT5SetupError(
                "MetaTrader5 Python package is required on Windows with the MT5 terminal installed."
            ) from exc

        if not mt5.initialize():
            raise MT5SetupError(f"MT5 initialize failed: {mt5.last_error()}")

        self._mt5 = mt5
        self.connected = True

    def account_state(self) -> AccountState:
        if self._mt5 is None:
            raise MT5SetupError("MT5Broker.connect() must be called before account_state()")
        info = self._mt5.account_info()
        if info is None:
            raise MT5SetupError(f"MT5 account_info failed: {self._mt5.last_error()}")
        return AccountState(
            equity=float(info.equity),
            balance=float(info.balance),
            daily_realized_pnl=0,
        )

    def place_order(self, intent: TradeIntent) -> OrderResult:
        if self._mt5 is None:
            raise MT5SetupError("MT5Broker.connect() must be called before place_order()")
        return OrderResult(False, None, "MT5 order execution remains disabled in V1 demo adapter")
```

- [ ] **Step 4: Add Windows setup notes**

Create `docs/windows-mt5-setup.md`:

```markdown
# Windows MetaTrader 5 Setup

V1 is safe by design: local paper mode works without MT5, and MT5 order execution remains disabled in the guarded demo adapter.

## Requirements

- Windows PC or Windows VPS.
- MetaTrader 5 terminal installed.
- Broker demo account logged into the MT5 terminal.
- Python 3.11 or newer.

## Install

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev,mt5]"
python -m forexbot check-config --config configs/paper.yaml
```

## Notes

- Do not store broker passwords in git.
- Use a demo account first.
- Keep AutoTrading disabled until a dedicated live-trading milestone adds explicit unlock controls.
- If your broker uses a gold symbol other than `XAUUSD`, edit `configs/paper.yaml` and `configs/backtest.yaml`.
```

- [ ] **Step 5: Run MT5 tests**

Run: `pytest tests/test_mt5_broker.py -v`

Expected: PASS on macOS without the `MetaTrader5` package installed.

- [ ] **Step 6: Commit MT5 adapter**

```bash
git add src/forexbot/mt5_broker.py docs/windows-mt5-setup.md tests/test_mt5_broker.py
git commit -m "feat: add guarded MT5 demo adapter"
```

---

## Task 10: Full Verification And Final Safety Pass

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with verified commands**

Replace `README.md` with:

```markdown
# Forexbot

Python trading bot for conservative forex paper trading and guarded MetaTrader 5 demo execution.

V1 is paper/demo focused. It does not unlock live trading.

## Safety Defaults

- Risk per trade: `0.25%`
- Max daily loss: `1%`
- Max open trades: `3`
- Max open trades per symbol: `1`
- No martingale or averaging down
- MT5 order execution disabled in V1 adapter

## Local Setup

```bash
python -m pip install -e ".[dev]"
pytest -v
```

## Commands

```bash
python -m forexbot check-config --config configs/paper.yaml
python -m forexbot run --config configs/paper.yaml --once
python -m forexbot backtest --config configs/backtest.yaml
```

## Windows MT5

Read `docs/windows-mt5-setup.md` before trying MT5 demo integration.
```

- [ ] **Step 2: Run the full test suite**

Run: `pytest -v`

Expected: all tests PASS.

- [ ] **Step 3: Run local commands**

Run: `python -m forexbot check-config --config configs/paper.yaml`

Expected: `OK: configs/paper.yaml mode=paper symbols=4`

Run: `python -m forexbot run --config configs/paper.yaml --once`

Expected: exits with code `0` and prints `paper summary`.

Run: `python -m forexbot backtest --config configs/backtest.yaml`

Expected: exits with code `0` and prints `backtest summary`.

- [ ] **Step 4: Verify no live trading unlock exists**

Run: `rg -n "live|allow_live|order_send|TRADE_ACTION_DEAL" src tests configs docs README.md`

Expected:

- `src/forexbot/config.py` rejects `mode: live`.
- `src/forexbot/mt5_broker.py` does not call `order_send`.
- Docs mention that live trading is locked.

- [ ] **Step 5: Commit final docs**

```bash
git add README.md
git commit -m "docs: document forexbot safety workflow"
```

---

## Self-Review

Spec coverage:

- Engine-first architecture: Tasks 1, 6, 7, and 8.
- Config and CLI: Tasks 2 and 8.
- Conservative trend strategy: Task 4.
- Risk controls: Task 5.
- Paper broker: Task 6.
- Journaled engine loop: Task 7.
- MT5 guarded Windows adapter: Task 9.
- Tests and smoke verification: Tasks 1 through 10.
- Live trading locked: Tasks 2, 9, and 10.

Placeholder scan:

- No banned marker phrases or empty implementation steps remain.
- Every code-producing task names exact files and includes runnable test or implementation content.

Type consistency:

- `SymbolConfig`, `RiskConfig`, `StrategyConfig`, `AccountState`, `Signal`, `TradeIntent`, and `OrderResult` are introduced before dependent tasks use them.
- `TradingEngine` constructor arguments match CLI wiring and engine tests.
- `PaperBroker` and `MT5Broker` both provide `account_state()` and `place_order()` methods.
