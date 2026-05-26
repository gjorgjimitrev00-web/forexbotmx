from pathlib import Path

import pytest

from forexbot.config import load_config
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
