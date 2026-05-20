from __future__ import annotations

from forexbot.models import Candle


def sma(values: list[float], period: int) -> float | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def atr(candles: list[Candle], period: int) -> float | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period + 1:
        return None

    true_ranges = []
    start = len(candles) - period
    for index in range(start, len(candles)):
        candle = candles[index]
        previous_close = candles[index - 1].close
        true_ranges.append(
            max(
                candle.high - candle.low,
                abs(candle.high - previous_close),
                abs(candle.low - previous_close),
            )
        )

    return round(sum(true_ranges) / period, 10)
