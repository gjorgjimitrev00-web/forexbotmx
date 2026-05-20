from datetime import datetime, timedelta, timezone
from dataclasses import replace
import math

from forexbot.config import StrategyConfig, SymbolConfig
from forexbot.models import Candle, Side
from forexbot.strategy import TrendFollowingStrategy


def make_candles(symbol: str, timeframe: str, start: float, step: float, count: int) -> list[Candle]:
    base = datetime(2026, 5, 20, tzinfo=timezone.utc)
    candles: list[Candle] = []
    for index in range(count):
        close = start + (step * index)
        candles.append(
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                time=base + timedelta(minutes=15 * index),
                open=close - (step / 2),
                high=close + 0.0010,
                low=close - 0.0010,
                close=close,
                volume=1000,
            )
        )
    return candles


def config() -> StrategyConfig:
    return StrategyConfig(
        fast_sma=3,
        slow_sma=5,
        atr_period=3,
        atr_stop_multiplier=1.5,
        take_profit_r_multiple=2.0,
        max_spread_points=20,
    )


def symbol() -> SymbolConfig:
    return SymbolConfig(
        name="EURUSD",
        point=0.0001,
        point_value_per_lot=10,
        min_volume=0.01,
        max_volume=1,
        volume_step=0.01,
    )


def test_returns_buy_when_m15_and_h1_trend_up():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=10)

    assert signal.side == Side.BUY
    assert signal.entry_price == m15[-1].close
    assert signal.stop_loss < signal.entry_price
    assert signal.take_profit > signal.entry_price


def test_returns_sell_when_m15_and_h1_trend_down():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1200, -0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.1400, -0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=10)

    assert signal.side == Side.SELL
    assert signal.stop_loss > signal.entry_price
    assert signal.take_profit < signal.entry_price


def test_holds_when_spread_is_too_high():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=25)

    assert signal.side == Side.HOLD
    assert "spread" in signal.reason


def test_holds_when_spread_is_nan():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=math.nan)

    assert signal.side == Side.HOLD
    assert "invalid spread" in signal.reason


def test_holds_when_spread_is_negative():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=-1)

    assert signal.side == Side.HOLD
    assert "invalid spread" in signal.reason


def test_holds_when_candle_data_is_not_finite():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    m15[-1] = replace(m15[-1], close=math.nan)
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=10)

    assert signal.side == Side.HOLD
    assert "invalid market data" in signal.reason


def test_holds_when_m15_and_h1_disagree():
    strategy = TrendFollowingStrategy(config())
    m15 = make_candles("EURUSD", "M15", 1.1000, 0.0010, 12)
    h1 = make_candles("EURUSD", "H1", 1.1400, -0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=10)

    assert signal.side == Side.HOLD
    assert signal.reason == "trend confirmation failed"


def test_holds_when_volatility_is_zero():
    strategy = TrendFollowingStrategy(config())
    m15 = [
        replace(candle, open=1.1000, high=1.1000, low=1.1000, close=1.1000)
        for candle in make_candles("EURUSD", "M15", 1.1000, 0, 12)
    ]
    h1 = make_candles("EURUSD", "H1", 1.0900, 0.0020, 12)

    signal = strategy.evaluate(symbol(), m15=m15, h1=h1, spread_points=10)

    assert signal.side == Side.HOLD
    assert "invalid market data" in signal.reason
