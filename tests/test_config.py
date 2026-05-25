from pathlib import Path

import pytest

from forexbot.config import ConfigError, load_config


def write_config(tmp_path, *, risk_per_trade_pct="0.25", market_data_path="data/sample_candles.json", symbol_lines=None):
    path = tmp_path / "config.yaml"
    symbol_lines = symbol_lines or [
        "  - name: EURUSD",
        "    point: 0.0001",
        "    point_value_per_lot: 10",
        "    min_volume: 0.01",
        "    max_volume: 1.0",
        "    volume_step: 0.01",
    ]
    path.write_text(
        f"""
mode: paper
account:
  starting_equity: 10000
risk:
  risk_per_trade_pct: {risk_per_trade_pct}
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
  path: {market_data_path}
symbols:
{chr(10).join(symbol_lines)}
""",
        encoding="utf-8",
    )
    return path


def test_loads_paper_config():
    config = load_config(Path("configs/paper.yaml"))

    assert config.mode == "paper"
    assert config.risk.risk_per_trade_pct == 0.25
    assert config.risk.max_daily_loss_pct == 1.0
    assert [symbol.name for symbol in config.symbols] == ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]


def test_loads_mt5_demo_config():
    config = load_config(Path("configs/mt5_demo.yaml"))

    assert config.mode == "mt5_demo"
    assert config.mt5 is not None
    assert config.mt5.account_number > 0
    assert config.mt5.magic == 260526


def test_mt5_modes_require_mt5_section(tmp_path):
    path = tmp_path / "missing-mt5.yaml"
    path.write_text(Path("configs/paper.yaml").read_text().replace("mode: paper", "mode: mt5_demo"), encoding="utf-8")

    with pytest.raises(ConfigError, match="mt5 section is required"):
        load_config(path)


def test_loads_mt5_live_example_config():
    config = load_config(Path("configs/mt5_live.example.yaml"))

    assert config.mode == "mt5_live"
    assert config.mt5 is not None
    assert config.mt5.account_number > 0


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


def test_rejects_non_finite_float(tmp_path):
    path = write_config(tmp_path, risk_per_trade_pct=".nan")

    with pytest.raises(ConfigError, match="risk_per_trade_pct"):
        load_config(path)


@pytest.mark.parametrize("market_data_path", ["null", "''"])
def test_rejects_empty_market_data_path(tmp_path, market_data_path):
    path = write_config(tmp_path, market_data_path=market_data_path)

    with pytest.raises(ConfigError, match="market_data.path"):
        load_config(path)


def test_rejects_symbol_min_volume_above_max_volume(tmp_path):
    path = write_config(
        tmp_path,
        symbol_lines=[
            "  - name: EURUSD",
            "    point: 0.0001",
            "    point_value_per_lot: 10",
            "    min_volume: 1.0",
            "    max_volume: 0.01",
            "    volume_step: 0.01",
        ],
    )

    with pytest.raises(ConfigError, match="min_volume"):
        load_config(path)


def test_rejects_symbol_volume_step_larger_than_range(tmp_path):
    path = write_config(
        tmp_path,
        symbol_lines=[
            "  - name: EURUSD",
            "    point: 0.0001",
            "    point_value_per_lot: 10",
            "    min_volume: 0.01",
            "    max_volume: 0.02",
            "    volume_step: 0.02",
        ],
    )

    with pytest.raises(ConfigError, match="volume_step"):
        load_config(path)
