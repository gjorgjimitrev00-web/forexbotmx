# Forexbot

Python trading bot for conservative forex paper trading, MetaTrader 5 demo execution, and guarded MT5 live execution.

## Safety Defaults

- Risk per trade: `0.25%`
- Max daily loss: `1%`
- Max open trades: `3`
- Max open trades per symbol: `1`
- No martingale or averaging down
- MT5 live mode requires `mode: mt5_live` plus exact account-number verification
- Broker passwords are never stored in config

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
python -m forexbot ui --config configs/paper.yaml --host 127.0.0.1 --port 8765
```

## Windows MT5

Read `docs/windows-mt5-setup.md` before using MT5 demo or live execution.
