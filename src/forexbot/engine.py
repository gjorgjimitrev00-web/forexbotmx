from __future__ import annotations

from typing import Any

from forexbot.broker import Broker
from forexbot.config import SymbolConfig
from forexbot.journal import JsonlJournal
from forexbot.market_data import MarketDataProvider
from forexbot.risk import RiskManager
from forexbot.strategy import TrendFollowingStrategy


class TradingEngine:
    def __init__(
        self,
        *,
        symbols: tuple[SymbolConfig, ...],
        market_data: MarketDataProvider,
        strategy: TrendFollowingStrategy,
        risk_manager: RiskManager,
        broker: Broker,
        journal: JsonlJournal,
        spread_points: dict[str, float],
    ) -> None:
        self.symbols = symbols
        self.market_data = market_data
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.broker = broker
        self.journal = journal
        self.spread_points = spread_points
        self._processed_candles: set[tuple[str, str]] = set()

    def run_once(self) -> dict[str, int]:
        summary = {
            "executed": 0,
            "blocked": 0,
            "held": 0,
            "duplicates": 0,
            "errors": 0,
        }

        for symbol in self.symbols:
            try:
                self._run_symbol(symbol, summary)
            except Exception as exc:  # pragma: no cover - exercised by callers with failing dependencies.
                summary["errors"] += 1
                self.journal.record(
                    "symbol_error",
                    symbol=symbol.name,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )

        return summary

    def _run_symbol(self, symbol: SymbolConfig, summary: dict[str, int]) -> None:
        m15 = self.market_data.recent_candles(symbol.name, "M15", limit=100)
        h1 = self.market_data.recent_candles(symbol.name, "H1", limit=100)
        latest = m15[-1]
        candle_time_iso = latest.time.isoformat()
        candle_key = (symbol.name, candle_time_iso)

        if candle_key in self._processed_candles:
            summary["duplicates"] += 1
            self.journal.record(
                "duplicate_candle_skipped",
                symbol=symbol.name,
                candle_time=candle_time_iso,
            )
            return

        self._processed_candles.add(candle_key)
        signal = self.strategy.evaluate(
            symbol,
            m15=m15,
            h1=h1,
            spread_points=self.spread_points.get(symbol.name, 0),
        )
        self.journal.record(
            "signal",
            symbol=symbol.name,
            side=signal.side.value,
            reason=signal.reason,
            candle_time=signal.candle_time,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
        )

        account = self.broker.account_state()
        decision = self.risk_manager.evaluate(symbol, account, signal)
        if not decision.allowed:
            if signal.side.value == "hold":
                summary["held"] += 1
            else:
                summary["blocked"] += 1
            self.journal.record(
                "trade_blocked",
                symbol=symbol.name,
                side=signal.side.value,
                reason=decision.reason,
            )
            return

        if decision.intent is None:
            summary["blocked"] += 1
            self.journal.record(
                "trade_blocked",
                symbol=symbol.name,
                side=signal.side.value,
                reason="risk decision missing intent",
            )
            return

        result = self.broker.place_order(decision.intent)
        order_fields: dict[str, Any] = {
            "symbol": symbol.name,
            "side": decision.intent.side.value,
            "volume": decision.intent.volume,
            "order_id": result.order_id,
            "message": result.message,
        }
        if result.accepted:
            summary["executed"] += 1
            self.journal.record("order_executed", **order_fields)
            return

        summary["blocked"] += 1
        self.journal.record("order_rejected", **order_fields)
