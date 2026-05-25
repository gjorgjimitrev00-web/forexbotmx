# MT5 Live Execution And Local UI V2 Design

Date: 2026-05-26

## Goal

Add real MetaTrader 5 execution for demo and live accounts, plus a local-only web control panel for operating the bot on Windows.

V2 must make the bot usable with MT5 while keeping live trading deliberate, visible, and bounded by the existing risk controls.

## Runtime

- Primary runtime: Windows PC or Windows VPS.
- MT5 terminal must be installed and logged in.
- UI binds to `127.0.0.1` only.
- macOS development must still support tests through fake MT5 modules.

## Modes

Supported modes:

- `paper`: local simulated execution.
- `backtest`: deterministic local backtest/smoke mode.
- `mt5_demo`: real MT5 orders on a demo account.
- `mt5_live`: real MT5 orders on a live account.

Live mode must not require an unlock phrase, per user request. It must still require explicit `mode: mt5_live` and account-number verification against config so a wrong terminal/account cannot trade silently.

## MT5 Execution

`MT5Broker` will become a real execution adapter:

- Connect with `MetaTrader5.initialize()`.
- Read account info with `account_info()`.
- Read open positions with `positions_get()`.
- Ensure the symbol is selected with `symbol_select()`.
- Read current bid/ask with `symbol_info_tick()`.
- Build market buy/sell requests with stop-loss and take-profit.
- Run `order_check()` before `order_send()`.
- Send with `order_send()` only after all local and MT5 checks pass.
- Return structured `OrderResult` values with ticket/retcode/message details.

The broker must reject execution when:

- Connected account number does not match configured account number.
- Terminal/account trade permissions are unavailable.
- Symbol is missing or cannot be selected.
- Tick data is missing.
- Spread exceeds config.
- `order_check()` fails.
- `order_send()` returns failure or `None`.

## Live Safety Rules

V2 live mode keeps these controls:

- Explicit `mode: mt5_live`.
- Configured account number must equal the connected MT5 account number.
- Existing risk manager remains mandatory.
- Stop-loss and take-profit are required.
- Max open trades and per-symbol exposure remain enforced.
- No martingale, no grid recovery, no averaging down.
- UI must clearly show when mode is `mt5_live`.
- UI controls must not default to live mode.

## UI

Use FastAPI with server-rendered/simple HTML, CSS, and minimal JavaScript.

The UI will provide:

- Current mode and account status.
- Config editor for mode, symbols, risk, strategy, spreads, and MT5 connection/account settings.
- Buttons for check config, run one cycle, backtest, and stop/disable loop controls.
- Recent signals, orders, blocks, errors, and journal entries.
- Clear visual warning when `mt5_live` is selected.

V2 does not need user accounts because it binds to `127.0.0.1` only. Public/LAN access is a non-goal.

## API

Local HTTP endpoints:

- `GET /` renders dashboard.
- `GET /api/config` returns current config.
- `POST /api/config` validates and saves config.
- `POST /api/check-config` validates config.
- `POST /api/run-once` runs one cycle for the selected mode.
- `POST /api/backtest` runs backtest mode.
- `GET /api/journal` returns recent journal entries.
- `GET /api/status` returns account, mode, and last summary.

All endpoints bind through the local FastAPI app only.

## Config Changes

Add MT5 config fields:

- `account_number`
- `terminal_path`
- `server`
- `magic`
- `deviation_points`
- `order_comment`
- `type_filling`

Sensitive values such as passwords must not be stored in git. V2 relies on an already logged-in MT5 terminal. Password-based login is out of scope for V2.

## Testing

Tests must use fake MT5 modules and must not require Windows or a broker connection.

Coverage must include:

- Demo/live mode config validation.
- Live account mismatch blocks execution.
- `order_check()` failure blocks `order_send()`.
- Successful fake MT5 send returns accepted `OrderResult`.
- BUY/SELL request fields are correct.
- UI/API config validation and run-once endpoints.
- Local-only host defaults.
- Existing paper/backtest tests remain green.

## Non-Goals

- No public web access.
- No password storage.
- No automatic login with stored broker credentials.
- No order closing/trailing stop management.
- No always-running background daemon unless started explicitly.
- No strategy redesign.
