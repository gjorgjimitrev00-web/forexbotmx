from __future__ import annotations

from forexbot.models import AccountState, OrderResult, TradeIntent


class MT5SetupError(RuntimeError):
    """Raised when MT5 is unavailable or not ready for broker access."""


class MT5Broker:
    def __init__(self) -> None:
        self.connected = False
        self._mt5 = None

    def connect(self) -> None:
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise MT5SetupError(
                "MetaTrader5 Python package is required on Windows with the MT5 terminal installed."
            ) from exc

        if not mt5.initialize():
            raise MT5SetupError(f"MT5 initialize failed: {mt5.last_error()}")

        self._mt5 = mt5
        self.connected = True

    def account_state(self) -> AccountState:
        if not self.connected or self._mt5 is None:
            raise MT5SetupError("MT5 broker is not connected.")

        account = self._mt5.account_info()
        if account is None:
            raise MT5SetupError(f"MT5 account_info failed: {self._mt5.last_error()}")

        return AccountState(
            equity=account.equity,
            balance=account.balance,
            daily_realized_pnl=0,
        )

    def place_order(self, intent: TradeIntent) -> OrderResult:
        if not self.connected or self._mt5 is None:
            raise MT5SetupError("MT5 broker is not connected.")

        return OrderResult(
            False,
            None,
            "MT5 order execution remains disabled in V1 demo adapter",
        )
