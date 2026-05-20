# Windows MetaTrader 5 Setup

V1 is safe by design. Local paper trading works without MetaTrader 5, and MT5
order execution is disabled in the guarded demo adapter.

## Requirements

- Windows PC or VPS
- MetaTrader 5 terminal
- Broker demo account logged in through the MT5 terminal
- Python 3.11+

## Install

Open PowerShell in the project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,mt5]"
forexbot check-config --config configs\paper.yaml
```

## Notes

- Do not store broker passwords in git.
- Use a demo account first.
- Keep AutoTrading disabled until the live trading milestone.
- Edit config if your broker's gold symbol differs from XAUUSD.
