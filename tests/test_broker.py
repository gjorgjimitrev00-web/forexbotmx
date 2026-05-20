from datetime import datetime, timezone

from forexbot.broker import PaperBroker
from forexbot.market_data import JsonMarketDataProvider
from forexbot.models import AccountState, Side, TradeIntent


def intent() -> TradeIntent:
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


def test_paper_broker_records_order():
    broker = PaperBroker(starting_equity=10000)

    result = broker.place_order(intent())

    assert result.accepted is True
    assert result.order_id == "paper-1"
    assert len(broker.orders) == 1


def test_paper_broker_exposes_account_state():
    broker = PaperBroker(starting_equity=10000)

    state = broker.account_state()

    assert isinstance(state, AccountState)
    assert state.equity == 10000


def test_json_market_data_provider_loads_symbol_timeframe():
    provider = JsonMarketDataProvider("data/sample_candles.json")

    candles = provider.recent_candles("EURUSD", "M15", limit=10)

    assert len(candles) == 10
    assert candles[-1].symbol == "EURUSD"
    assert candles[-1].time.tzinfo is not None
