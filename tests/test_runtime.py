from pathlib import Path
from types import SimpleNamespace

import pytest

from forexbot.config import load_config
from forexbot.mt5_market_data import MT5MarketDataProvider
from forexbot.runtime import build_engine_from_config
from tests.fakes import FakeMT5


@pytest.fixture
def fake_mt5_module() -> FakeMT5:
    return FakeMT5()


def test_paper_runtime_uses_paper_components(tmp_path):
    config = load_config(Path("configs/paper.yaml"))

    engine = build_engine_from_config(config, tmp_path / "paper.jsonl")

    assert engine.broker.__class__.__name__ == "PaperBroker"


def test_mt5_runtime_uses_mt5_components(tmp_path, fake_mt5_module):
    config = load_config(Path("configs/mt5_demo.yaml"))

    engine = build_engine_from_config(config, tmp_path / "mt5.jsonl", mt5_module=fake_mt5_module)

    assert engine.broker.__class__.__name__ == "MT5Broker"
    assert engine.market_data.__class__.__name__ == "MT5MarketDataProvider"


def test_mt5_market_data_uses_object_row_volume_when_tick_volume_missing(fake_mt5_module):
    fake_mt5_module.rates[fake_mt5_module.TIMEFRAME_M15] = [
        SimpleNamespace(
            time=1_779_292_800,
            open=1.1,
            high=1.2,
            low=1.0,
            close=1.15,
            volume=123,
        )
    ]
    provider = MT5MarketDataProvider(fake_mt5_module)

    candles = provider.recent_candles("EURUSD", "M15", 1)

    assert candles[0].volume == 123.0
