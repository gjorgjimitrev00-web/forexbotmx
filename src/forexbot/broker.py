from __future__ import annotations

from typing import Protocol

from forexbot.models import AccountState, OrderResult, Position, TradeIntent


class Broker(Protocol):
    def account_state(self) -> AccountState:
        """Return current account state."""

    def place_order(self, intent: TradeIntent) -> OrderResult:
        """Place an order for a trade intent."""


class PaperBroker:
    def __init__(self, starting_equity: float) -> None:
        self.starting_equity = starting_equity
        self.orders: list[TradeIntent] = []

    def account_state(self) -> AccountState:
        return AccountState(
            equity=self.starting_equity,
            balance=self.starting_equity,
            daily_realized_pnl=0,
            open_positions=tuple(
                Position(
                    symbol=order.symbol,
                    side=order.side,
                    volume=order.volume,
                    entry_price=order.entry_price,
                    stop_loss=order.stop_loss,
                    opened_at=order.candle_time,
                )
                for order in self.orders
            ),
        )

    def place_order(self, intent: TradeIntent) -> OrderResult:
        if intent.volume <= 0:
            return OrderResult(False, None, "volume must be positive")

        self.orders.append(intent)
        return OrderResult(True, f"paper-{len(self.orders)}", "paper order accepted")
