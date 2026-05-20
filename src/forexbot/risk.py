from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from math import isfinite

from forexbot.config import RiskConfig, SymbolConfig
from forexbot.models import AccountState, Side, Signal, TradeIntent


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    intent: TradeIntent | None = None


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def evaluate(self, symbol: SymbolConfig, account: AccountState, signal: Signal) -> RiskDecision:
        if signal.side == Side.HOLD:
            return RiskDecision(False, signal.reason)

        if (
            signal.entry_price is None
            or signal.stop_loss is None
            or signal.take_profit is None
            or signal.candle_time is None
        ):
            return RiskDecision(False, "signal is missing required order prices")

        if not all(
            isfinite(value)
            for value in (
                signal.entry_price,
                signal.stop_loss,
                signal.take_profit,
                account.equity,
                account.daily_realized_pnl,
            )
        ):
            return RiskDecision(False, "signal or account contains non-finite value")

        if signal.side == Side.BUY and not (signal.stop_loss < signal.entry_price < signal.take_profit):
            return RiskDecision(False, "invalid buy price direction")

        if signal.side == Side.SELL and not (signal.take_profit < signal.entry_price < signal.stop_loss):
            return RiskDecision(False, "invalid sell price direction")

        if len(account.open_positions) >= self.config.max_open_trades:
            return RiskDecision(False, "max open trades reached")

        symbol_positions = sum(1 for position in account.open_positions if position.symbol == symbol.name)
        if symbol_positions >= self.config.max_open_trades_per_symbol:
            return RiskDecision(False, "per-symbol open trade limit reached")

        daily_loss_limit = account.equity * (self.config.max_daily_loss_pct / 100)
        if account.daily_realized_pnl <= -daily_loss_limit:
            return RiskDecision(False, "daily loss limit reached")

        volume = self._position_size(symbol, account.equity, signal.entry_price, signal.stop_loss)
        if volume < symbol.min_volume:
            return RiskDecision(False, "calculated volume below minimum")

        return RiskDecision(
            allowed=True,
            reason="risk checks passed",
            intent=TradeIntent(
                symbol=symbol.name,
                side=signal.side,
                volume=volume,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                reason=signal.reason,
                candle_time=signal.candle_time,
            ),
        )

    def _position_size(self, symbol: SymbolConfig, equity: float, entry: float, stop: float) -> float:
        stop_points = abs(entry - stop) / symbol.point
        if stop_points <= 0:
            return 0

        risk_amount = equity * (self.config.risk_per_trade_pct / 100)
        raw_volume = risk_amount / (stop_points * symbol.point_value_per_lot)
        bounded_volume = min(max(raw_volume, symbol.min_volume), symbol.max_volume)

        step = Decimal(str(symbol.volume_step))
        steps = (Decimal(str(bounded_volume)) / step).to_integral_value(rounding=ROUND_DOWN)
        volume = steps * step
        return float(volume)
