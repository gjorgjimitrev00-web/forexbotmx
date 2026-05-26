# Windows MetaTrader 5 Setup

Local paper trading works without MetaTrader 5. MT5 demo and live modes use the
logged-in desktop terminal, verify the configured account number, run
`order_check()` before `order_send()`, and keep the control panel bound to a
local host.

## Requirements

- Windows PC or VPS
- MetaTrader 5 terminal
- Broker demo or live account logged in through the MT5 terminal
- Python 3.11+

## Install

Open PowerShell in the project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,mt5]"
forexbot check-config --config configs\paper.yaml
python -m forexbot ui --config configs\paper.yaml --host 127.0.0.1 --port 8765
```

## Demo Flow

1. Start MetaTrader 5.
2. Log into your broker demo account in the MT5 terminal.
3. Edit `configs\mt5_demo.yaml` and set `mt5.account_number` to the exact account shown in MT5.
4. If your broker uses a different gold symbol, edit the `XAUUSD` symbol name.
5. Run:

```powershell
python -m forexbot ui --config configs\mt5_demo.yaml --host 127.0.0.1 --port 8765
```

6. Open `http://127.0.0.1:8765`.
7. Use Check Config first, then Run One Cycle.

## Live Flow

1. Copy `configs\mt5_live.example.yaml` to a private local config, such as `configs\mt5_live.local.yaml`.
2. Keep `mode: mt5_live`.
3. Set `mt5.account_number` to the exact connected live account.
4. Verify all risk values, symbols, lot constraints, spread limit, terminal path, server, magic, deviation, comment, and filling mode.
5. Run the UI local-only:

```powershell
python -m forexbot ui --config configs\mt5_live.local.yaml --host 127.0.0.1 --port 8765
```

6. Use Check Config before any Run One Cycle action.

## Notes

- Do not store broker passwords in git.
- Use a demo account first.
- Keep AutoTrading disabled until you are ready to place real orders.
- Edit config if your broker's gold symbol differs from XAUUSD.
- Live trading can lose money. Start with the smallest allowed volume.
