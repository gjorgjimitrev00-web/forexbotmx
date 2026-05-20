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
