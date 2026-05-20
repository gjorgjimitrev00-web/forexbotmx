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
