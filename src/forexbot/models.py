from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side
    reason: str
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    candle_time: datetime | None = None


@dataclass(frozen=True)
class TradeIntent:
    symbol: str
    side: Side
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    candle_time: datetime

    def __post_init__(self) -> None:
        _validate_tradeable_side(self.side)


@dataclass(frozen=True)
class Position:
    symbol: str
    side: Side
    volume: float
    entry_price: float
    stop_loss: float
    opened_at: datetime

    def __post_init__(self) -> None:
        _validate_tradeable_side(self.side)


@dataclass(frozen=True)
class AccountState:
    equity: float
    balance: float
    daily_realized_pnl: float
    open_positions: tuple[Position, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OrderResult:
    accepted: bool
    order_id: str | None
    message: str


def _validate_tradeable_side(side: Side) -> None:
    if side not in {Side.BUY, Side.SELL}:
        raise ValueError("side must be buy or sell")
