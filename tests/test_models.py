from datetime import datetime, timezone

import pytest

from forexbot.models import Position, Side, TradeIntent


def utc_now() -> datetime:
    return datetime(2026, 5, 20, tzinfo=timezone.utc)


def test_trade_intent_rejects_hold_side():
    with pytest.raises(ValueError, match="side must be buy or sell"):
        TradeIntent(
            symbol="EURUSD",
            side=Side.HOLD,
            volume=0.1,
            entry_price=1.1050,
            stop_loss=1.1000,
            take_profit=1.1150,
            reason="no executable signal",
            candle_time=utc_now(),
        )


def test_position_rejects_hold_side():
    with pytest.raises(ValueError, match="side must be buy or sell"):
        Position(
            symbol="EURUSD",
            side=Side.HOLD,
            volume=0.1,
            entry_price=1.1050,
            stop_loss=1.1000,
            opened_at=utc_now(),
        )
