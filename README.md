# Forexbot

Python trading bot for conservative forex paper trading and guarded MetaTrader 5 demo execution.

V1 is paper/demo focused. It does not unlock live trading.

## Commands

```bash
python -m forexbot check-config --config configs/paper.yaml
python -m forexbot run --config configs/paper.yaml --once
python -m forexbot backtest --config configs/backtest.yaml
```
