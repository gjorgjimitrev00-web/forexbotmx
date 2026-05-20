# Forex MT5 Bot V1 Design

Date: 2026-05-20

## Goal

Build a Python forex trading bot that can be developed and tested on macOS, then run on Windows with MetaTrader 5 installed. V1 prioritizes safety, testability, and a conservative starter strategy over broad features.

The first release must support paper/demo trading only. Live trading remains locked until a future milestone adds explicit unlock controls and additional verification.

## Target Runtime

- Development workspace: macOS/Codex.
- Live integration target: Windows PC or VPS with MetaTrader 5 installed and logged in.
- MT5 bridge: official `MetaTrader5` Python package, isolated behind an adapter so the core bot remains testable without MT5.

## Trading Scope

Initial symbols:

- `EURUSD`
- `GBPUSD`
- `USDJPY`
- Gold as `XAUUSD`. V1 config must allow the user to replace this with a broker-specific symbol name.

Trading style:

- Conservative trend-following.
- Primary timeframes: `M15` and `H1`.
- No high-frequency trading.
- No martingale, no averaging down, no doubling after losses.

## Architecture

The bot will be built as an engine-first Python package. Core trading logic must not import MT5 directly.

Main flow:

```text
Market Data -> Strategy -> Risk Manager -> Broker Adapter -> Journal
```

Adapters:

- `PaperBroker`: local simulated execution for development and tests.
- `MT5Broker`: Windows-only adapter for MetaTrader 5 demo execution.

The strategy produces trade intents. The risk manager decides whether a trade is allowed. The broker adapter handles execution or simulation. The journal records every decision.

## Components

`config`

- Load YAML config files.
- Validate symbols, timeframes, mode, risk limits, and broker settings.
- Reject unsafe settings for V1.

`market_data`

- Define candle data structures.
- Provide interfaces for historical and recent candles.
- Support paper/backtest data sources in V1 and expose the same interface for MT5 market data.

`strategy`

- Implement a starter trend-following strategy.
- Produce `buy`, `sell`, or `hold` decisions.
- Use deterministic, testable rules.

`risk`

- Calculate position size from account equity, stop distance, and configured risk.
- Enforce risk per trade, daily loss limit, max open trades, and per-symbol exposure.
- Require stop-loss on every trade.

`broker`

- Define a broker interface.
- Implement `PaperBroker` for local simulation.
- Implement a guarded `MT5Broker` that imports `MetaTrader5` only when needed.

`engine`

- Orchestrate config, market data, strategy, risk, broker, and journal.
- Run on a schedule and avoid duplicate trades on the same candle.

`journal`

- Write structured logs for each cycle.
- Record signals, blocked trades, accepted trades, order results, and errors.

`cli`

- Provide command-line entry points for config validation, paper running, and backtesting.

## CLI Commands

Initial commands:

```bash
python -m forexbot check-config --config configs/paper.yaml
python -m forexbot run --config configs/paper.yaml
python -m forexbot backtest --config configs/backtest.yaml
```

V1 defaults to paper/demo mode. Commands must make the selected mode obvious in logs.

## Starter Strategy

The starter strategy should be conservative and explainable:

- Use moving-average trend alignment on `M15` and `H1`.
- Use a volatility measure such as ATR for stop distance.
- Skip trades when spread is above the configured limit.
- Skip trades when recent candles fail the configured trend, volatility, or candle-close confirmation checks.
- Place both stop-loss and take-profit with each trade intent.

Exact indicator parameters will be finalized during implementation, but they must be configurable and covered by tests.

## Risk Controls

Default risk settings:

- Risk per trade: `0.25%` of account equity.
- Max daily loss: `1%` of account equity.
- Max open trades: `3` total.
- Max open trades per symbol: `1`.
- Stop-loss required for every trade.
- Spread filter required before execution.
- Paper/demo locked in V1.

The bot must block trades instead of silently adjusting them when risk constraints fail.

## Error Handling

- Config errors fail fast with clear messages.
- Data fetch failures are logged and skipped for that symbol/cycle.
- Strategy errors do not crash the entire loop if isolated to one symbol.
- Broker errors are recorded in the journal.
- MT5 import or connection failures explain the Windows/MT5 requirement.

## Testing

V1 tests must cover:

- Config validation rejects unsafe or malformed settings.
- Strategy returns predictable signals for sample candles.
- Risk manager blocks trades above limits.
- Position sizing respects `0.25%` risk.
- Paper broker records orders without touching MT5.
- Engine loop logs decisions and does not place duplicate trades on the same candle.

## First Milestone

1. Create the Python package and config files.
2. Implement paper trading end to end.
3. Add the starter trend-following strategy.
4. Add tests for config, strategy, risk, paper broker, and engine behavior.
5. Add a guarded MT5 adapter with Windows setup notes.
6. Run a local paper-mode smoke test.

## Non-Goals For V1

- No live trading unlock.
- No local web dashboard.
- No machine-learning model.
- No news trading.
- No martingale or grid recovery.
- No broker-specific symbol discovery beyond configurable symbol names.
