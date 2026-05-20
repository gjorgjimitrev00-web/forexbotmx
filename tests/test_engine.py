import json

from forexbot.broker import PaperBroker
from forexbot.config import RiskConfig, StrategyConfig, SymbolConfig
from forexbot.engine import TradingEngine
from forexbot.journal import JsonlJournal
from forexbot.market_data import JsonMarketDataProvider
from forexbot.risk import RiskManager
from forexbot.strategy import TrendFollowingStrategy


def test_engine_runs_one_cycle_and_journals_result(tmp_path):
    journal_path = tmp_path / "journal.jsonl"
    symbol = SymbolConfig("EURUSD", 0.0001, 10, 0.01, 1.0, 0.01)
    strategy = TrendFollowingStrategy(
        StrategyConfig(
            fast_sma=3,
            slow_sma=5,
            atr_period=3,
            atr_stop_multiplier=1.5,
            take_profit_r_multiple=2.0,
            max_spread_points=20,
        )
    )
    engine = TradingEngine(
        symbols=(symbol,),
        market_data=JsonMarketDataProvider("data/sample_candles.json"),
        strategy=strategy,
        risk_manager=RiskManager(RiskConfig(0.25, 1.0, 3, 1)),
        broker=PaperBroker(starting_equity=10000),
        journal=JsonlJournal(journal_path),
        spread_points={"EURUSD": 10},
    )

    summary = engine.run_once()

    assert summary["executed"] == 1
    entries = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()]
    assert entries[-1]["event"] == "order_executed"


def test_engine_skips_duplicate_candle(tmp_path):
    journal_path = tmp_path / "journal.jsonl"
    symbol = SymbolConfig("EURUSD", 0.0001, 10, 0.01, 1.0, 0.01)
    strategy = TrendFollowingStrategy(
        StrategyConfig(3, 5, 3, 1.5, 2.0, 20)
    )
    broker = PaperBroker(starting_equity=10000)
    engine = TradingEngine(
        symbols=(symbol,),
        market_data=JsonMarketDataProvider("data/sample_candles.json"),
        strategy=strategy,
        risk_manager=RiskManager(RiskConfig(0.25, 1.0, 3, 1)),
        broker=broker,
        journal=JsonlJournal(journal_path),
        spread_points={"EURUSD": 10},
    )

    first = engine.run_once()
    second = engine.run_once()

    assert first["executed"] == 1
    assert second["duplicates"] == 1
    assert len(broker.orders) == 1
