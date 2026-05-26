from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from forexbot.models import Candle


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
            time_value = row["time"] if isinstance(row, dict) else row.time
            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    time=datetime.fromtimestamp(int(time_value), timezone.utc),
                    open=float(row["open"] if isinstance(row, dict) else row.open),
                    high=float(row["high"] if isinstance(row, dict) else row.high),
                    low=float(row["low"] if isinstance(row, dict) else row.low),
                    close=float(row["close"] if isinstance(row, dict) else row.close),
                    volume=float(
                        row.get("tick_volume", row.get("volume", 0))
                        if isinstance(row, dict)
                        else getattr(row, "tick_volume", getattr(row, "volume", 0))
                    ),
                )
            )
        return candles
