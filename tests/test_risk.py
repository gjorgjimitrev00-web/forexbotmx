from dataclasses import replace
from datetime import datetime, timezone
from math import inf, nan

import pytest

from forexbot.config import RiskConfig, SymbolConfig
from forexbot.models import AccountState, Position, Side, Signal
from forexbot.risk import RiskManager


def risk() -> RiskConfig:
    return RiskConfig(
        risk_per_trade_pct=0.25,
        max_daily_loss_pct=1.0,
        max_open_trades=3,
        max_open_trades_per_symbol=1,
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


def buy_signal() -> Signal:
    return Signal(
        symbol="EURUSD",
        side=Side.BUY,
        reason="test",
        entry_price=1.1050,
        stop_loss=1.1000,
        take_profit=1.1150,
        candle_time=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )


def sell_signal() -> Signal:
    return Signal(
        symbol="EURUSD",
        side=Side.SELL,
        reason="test",
        entry_price=1.1050,
        stop_loss=1.1100,
        take_profit=1.0950,
        candle_time=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )


def test_sizes_position_from_risk_and_stop_distance():
    manager = RiskManager(risk())
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=0)

    decision = manager.evaluate(symbol(), account, buy_signal())

    assert decision.allowed is True
    assert decision.intent is not None
    assert decision.intent.volume == 0.05


def test_sizes_position_rounds_down_to_volume_step_multiple():
    manager = RiskManager(risk())
    stepped_symbol = SymbolConfig(
        name="EURUSD",
        point=0.0001,
        point_value_per_lot=10,
        min_volume=0.25,
        max_volume=10,
        volume_step=0.25,
    )
    signal = Signal(
        symbol="EURUSD",
        side=Side.BUY,
        reason="test",
        entry_price=1.1001,
        stop_loss=1.1000,
        take_profit=1.1010,
        candle_time=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )
    account = AccountState(equity=2520, balance=2520, daily_realized_pnl=0)

    decision = manager.evaluate(stepped_symbol, account, signal)

    assert decision.allowed is True
    assert decision.intent is not None
    assert decision.intent.volume == 0.5


def test_blocks_when_true_risk_size_is_below_minimum_volume():
    manager = RiskManager(risk())
    wide_stop_signal = replace(buy_signal(), stop_loss=0.1050)
    account = AccountState(equity=1000, balance=1000, daily_realized_pnl=0)

    decision = manager.evaluate(symbol(), account, wide_stop_signal)

    assert decision.allowed is False
    assert "below minimum" in decision.reason


@pytest.mark.parametrize("non_finite", [nan, inf])
@pytest.mark.parametrize("field", ["entry_price", "stop_loss", "take_profit"])
def test_blocks_non_finite_signal_prices(field: str, non_finite: float):
    manager = RiskManager(risk())
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=0)
    signal = replace(buy_signal(), **{field: non_finite})

    decision = manager.evaluate(symbol(), account, signal)

    assert decision.allowed is False
    assert "non-finite" in decision.reason


@pytest.mark.parametrize("non_finite", [nan, inf])
@pytest.mark.parametrize("field", ["equity", "balance", "daily_realized_pnl"])
def test_blocks_non_finite_account_values(field: str, non_finite: float):
    manager = RiskManager(risk())
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=0)
    account = replace(account, **{field: non_finite})

    decision = manager.evaluate(symbol(), account, buy_signal())

    assert decision.allowed is False
    assert "non-finite" in decision.reason


@pytest.mark.parametrize(
    ("signal", "expected_reason"),
    [
        (replace(buy_signal(), stop_loss=1.1060), "buy price direction"),
        (replace(buy_signal(), take_profit=1.1040), "buy price direction"),
        (replace(sell_signal(), stop_loss=1.1040), "sell price direction"),
        (replace(sell_signal(), take_profit=1.1060), "sell price direction"),
    ],
)
def test_blocks_invalid_stop_and_target_direction(signal: Signal, expected_reason: str):
    manager = RiskManager(risk())
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=0)

    decision = manager.evaluate(symbol(), account, signal)

    assert decision.allowed is False
    assert expected_reason in decision.reason


def test_blocks_when_daily_loss_limit_reached():
    manager = RiskManager(risk())
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=-100)

    decision = manager.evaluate(symbol(), account, buy_signal())

    assert decision.allowed is False
    assert "daily loss" in decision.reason


def test_blocks_when_symbol_already_has_open_position():
    manager = RiskManager(risk())
    position = Position(
        symbol="EURUSD",
        side=Side.BUY,
        volume=0.01,
        entry_price=1.1000,
        stop_loss=1.0950,
        opened_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )
    account = AccountState(equity=10000, balance=10000, daily_realized_pnl=0, open_positions=(position,))

    decision = manager.evaluate(symbol(), account, buy_signal())

    assert decision.allowed is False
    assert "per-symbol" in decision.reason
