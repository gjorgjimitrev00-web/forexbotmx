import builtins
import importlib
import sys

import pytest

from forexbot.mt5_broker import MT5Broker, MT5SetupError


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

        def initialize(self):
            return self.initialize_results.pop(0)

        def last_error(self):
            return (1, "failed reconnect")

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
