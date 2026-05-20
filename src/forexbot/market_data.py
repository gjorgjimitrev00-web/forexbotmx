from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

from forexbot.models import Candle


class MarketDataProvider(Protocol):
    def recent_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        """Return the most recent candles for a symbol and timeframe."""


class JsonMarketDataProvider:
    def __init__(self, path: str | Path) -> None:
        self._raw = json.loads(Path(path).read_text(encoding="utf-8"))

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
