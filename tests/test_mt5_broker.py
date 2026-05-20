import builtins

import pytest

from forexbot.mt5_broker import MT5Broker, MT5SetupError


def test_importing_mt5_broker_does_not_import_metatrader5():
    broker = MT5Broker()

    assert broker.connected is False


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
