import builtins
import importlib
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from forexbot.config import MT5Config
from forexbot.models import Side, TradeIntent
from forexbot.mt5_broker import MT5Broker, MT5SetupError
from tests.fakes import FakeMT5


def mt5_config(account_number: int = 12345678) -> MT5Config:
    return MT5Config(
        account_number=account_number,
        terminal_path=None,
        server=None,
        magic=20260520,
        deviation_points=10,
        order_comment="test order",
        type_filling="return",
    )


@pytest.fixture
def fake_mt5_module() -> FakeMT5:
    return FakeMT5()


def connected_broker(fake_mt5_module: FakeMT5) -> MT5Broker:
    broker = MT5Broker(mt5_config(), mode="mt5_live", mt5_module=fake_mt5_module)
    broker.connect()
    return broker


def buy_intent() -> TradeIntent:
    return TradeIntent(
        symbol="EURUSD",
        side=Side.BUY,
        volume=0.05,
        entry_price=1.1050,
        stop_loss=1.1000,
        take_profit=1.1150,
        reason="test",
        candle_time=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )


def test_importing_mt5_broker_does_not_import_metatrader5(monkeypatch):
    real_import = builtins.__import__
    mt5_imports = []

    def spy_import(name, *args, **kwargs):
        if name == "MetaTrader5":
            mt5_imports.append(name)
            raise AssertionError("MetaTrader5 should not be imported at module import time")
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "forexbot.mt5_broker", raising=False)
    monkeypatch.setattr(builtins, "__import__", spy_import)

    mt5_broker = importlib.import_module("forexbot.mt5_broker")
    broker = mt5_broker.MT5Broker()

    assert broker.connected is False
    assert mt5_imports == []


def test_connect_explains_missing_metatrader5(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "MetaTrader5":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    broker = MT5Broker()

    with pytest.raises(MT5SetupError, match="Windows"):
        broker.connect()


def test_failed_reconnect_clears_previous_mt5_state(monkeypatch):
    class FakeMT5:
        def __init__(self) -> None:
            self.initialize_results = [True, False]
            self.shutdown_calls = 0
            self.account = SimpleNamespace(login=12345678, equity=10000.0, balance=10000.0, trade_allowed=True)
            self.terminal = SimpleNamespace(trade_allowed=True)

        def initialize(self):
            return self.initialize_results.pop(0)

        def shutdown(self):
            self.shutdown_calls += 1

        def last_error(self):
            return (1, "failed reconnect")

        def account_info(self):
            return self.account

        def terminal_info(self):
            return self.terminal

    fake_mt5 = FakeMT5()
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "MetaTrader5":
            return fake_mt5
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    broker = MT5Broker()
    broker.connect()

    with pytest.raises(MT5SetupError, match="MT5 initialize failed"):
        broker.connect()

    assert broker.connected is False
    assert broker._mt5 is None
    assert fake_mt5.shutdown_calls == 1


def test_live_account_mismatch_blocks_execution(fake_mt5_module):
    broker = MT5Broker(mt5_config(account_number=999), mode="mt5_live", mt5_module=fake_mt5_module)
    with pytest.raises(MT5SetupError, match="account"):
        broker.connect()
    assert fake_mt5_module.shutdown_calls == 1
    assert broker.connected is False


def test_order_check_failure_blocks_order_send(fake_mt5_module):
    fake_mt5_module.check_result.retcode = 10013
    broker = connected_broker(fake_mt5_module)

    result = broker.place_order(buy_intent())

    assert result.accepted is False
    assert fake_mt5_module.sent_requests == []


def test_successful_buy_sends_checked_mt5_request(fake_mt5_module):
    broker = connected_broker(fake_mt5_module)

    result = broker.place_order(buy_intent())

    assert result.accepted is True
    request = fake_mt5_module.sent_requests[0]
    assert request["action"] == fake_mt5_module.TRADE_ACTION_DEAL
    assert request["type"] == fake_mt5_module.ORDER_TYPE_BUY
    assert request["price"] == fake_mt5_module.tick.ask
    assert request["sl"] == buy_intent().stop_loss
    assert request["tp"] == buy_intent().take_profit
