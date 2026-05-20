from datetime import datetime, timezone

from forexbot.indicators import atr, sma
from forexbot.models import Candle


def candle(high: float, low: float, close: float) -> Candle:
    return Candle(
        symbol="EURUSD",
        timeframe="M15",
        time=datetime(2026, 5, 20, tzinfo=timezone.utc),
        open=close,
        high=high,
        low=low,
        close=close,
        volume=1000,
    )


def test_sma_uses_last_period_values():
    assert sma([1, 2, 3, 4, 5], 3) == 4


def test_sma_returns_none_without_enough_values():
    assert sma([1, 2], 3) is None


def test_atr_uses_true_range_average():
    candles = [
        candle(1.1050, 1.1000, 1.1020),
        candle(1.1080, 1.1010, 1.1070),
        candle(1.1090, 1.1040, 1.1050),
    ]

    assert atr(candles, 2) == 0.006
