from __future__ import annotations

import math

from forexbot import indicators
from forexbot.config import StrategyConfig, SymbolConfig
from forexbot.models import Candle, Side, Signal


class TrendFollowingStrategy:
    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    def evaluate(
        self,
        symbol: SymbolConfig,
        *,
        m15: list[Candle],
        h1: list[Candle],
        spread_points: float,
    ) -> Signal:
        if not math.isfinite(spread_points) or spread_points < 0:
            return Signal(symbol=symbol.name, side=Side.HOLD, reason="invalid spread")

        if spread_points > self.config.max_spread_points:
            return Signal(symbol=symbol.name, side=Side.HOLD, reason="spread too high")

        latest = m15[-1] if m15 else None
        if len(m15) < max(self.config.slow_sma, self.config.atr_period + 1) or len(h1) < self.config.slow_sma:
            return Signal(
                symbol=symbol.name,
                side=Side.HOLD,
                reason="not enough candles",
                candle_time=latest.time if latest else None,
            )

        latest = m15[-1]
        prior = m15[-2]
        if not _candles_have_finite_prices(m15) or not _candles_have_finite_prices(h1):
            return Signal(
                symbol=symbol.name,
                side=Side.HOLD,
                reason="invalid market data",
                candle_time=latest.time,
            )

        m15_closes = [candle.close for candle in m15]
        h1_closes = [candle.close for candle in h1]

        m15_fast = indicators.sma(m15_closes, self.config.fast_sma)
        m15_slow = indicators.sma(m15_closes, self.config.slow_sma)
        h1_fast = indicators.sma(h1_closes, self.config.fast_sma)
        h1_slow = indicators.sma(h1_closes, self.config.slow_sma)
        volatility = indicators.atr(m15, self.config.atr_period)

        if (
            m15_fast is None
            or m15_slow is None
            or h1_fast is None
            or h1_slow is None
            or volatility is None
            or not _finite_values(m15_fast, m15_slow, h1_fast, h1_slow, volatility)
            or volatility <= 0
        ):
            return Signal(
                symbol=symbol.name,
                side=Side.HOLD,
                reason="invalid market data",
                candle_time=latest.time,
            )

        trend_up = m15_fast > m15_slow and h1_fast > h1_slow and latest.close > prior.close
        trend_down = m15_fast < m15_slow and h1_fast < h1_slow and latest.close < prior.close
        stop_distance = volatility * self.config.atr_stop_multiplier

        if trend_up:
            stop_loss = latest.close - stop_distance
            take_profit = latest.close + (stop_distance * self.config.take_profit_r_multiple)
            if not _finite_values(latest.close, stop_loss, take_profit):
                return Signal(
                    symbol=symbol.name,
                    side=Side.HOLD,
                    reason="invalid market data",
                    candle_time=latest.time,
                )
            return Signal(
                symbol=symbol.name,
                side=Side.BUY,
                reason="M15 and H1 trend up",
                entry_price=latest.close,
                stop_loss=stop_loss,
                take_profit=take_profit,
                candle_time=latest.time,
            )

        if trend_down:
            stop_loss = latest.close + stop_distance
            take_profit = latest.close - (stop_distance * self.config.take_profit_r_multiple)
            if not _finite_values(latest.close, stop_loss, take_profit):
                return Signal(
                    symbol=symbol.name,
                    side=Side.HOLD,
                    reason="invalid market data",
                    candle_time=latest.time,
                )
            return Signal(
                symbol=symbol.name,
                side=Side.SELL,
                reason="M15 and H1 trend down",
                entry_price=latest.close,
                stop_loss=stop_loss,
                take_profit=take_profit,
                candle_time=latest.time,
            )

        return Signal(
            symbol=symbol.name,
            side=Side.HOLD,
            reason="trend confirmation failed",
            candle_time=latest.time,
        )


def _candles_have_finite_prices(candles: list[Candle]) -> bool:
    return all(
        _finite_values(candle.open, candle.high, candle.low, candle.close)
        for candle in candles
    )


def _finite_values(*values: float) -> bool:
    return all(math.isfinite(value) for value in values)
