from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from forexbot.models import Candle


_MISSING = object()

TIMEFRAMES = {
    "M15": "TIMEFRAME_M15",
    "H1": "TIMEFRAME_H1",
}


class MT5MarketDataProvider:
    def __init__(self, mt5_module: Any) -> None:
        self._mt5 = mt5_module

    def recent_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        mt5_timeframe = getattr(self._mt5, TIMEFRAMES[timeframe])
        rows = self._mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, limit)
        if rows is None:
            raise RuntimeError(f"MT5 rates unavailable for {symbol} {timeframe}: {self._mt5.last_error()}")

        candles: list[Candle] = []
        for row in rows:
            time_value = _row_value(row, "time")
            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    time=datetime.fromtimestamp(int(time_value), timezone.utc),
                    open=float(_row_value(row, "open")),
                    high=float(_row_value(row, "high")),
                    low=float(_row_value(row, "low")),
                    close=float(_row_value(row, "close")),
                    volume=float(_row_value(row, "tick_volume", _row_value(row, "volume", 0))),
                )
            )
        return candles


def _row_value(row: Any, key: str, default: Any = _MISSING) -> Any:
    if isinstance(row, dict):
        return row.get(key, default) if default is not _MISSING else row[key]
    try:
        return row[key]
    except (KeyError, TypeError, IndexError, ValueError):
        value = getattr(row, key, default)
        if value is _MISSING:
            raise
        return value
