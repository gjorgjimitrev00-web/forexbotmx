from __future__ import annotations

from typing import Any

from forexbot.config import MT5Config
from forexbot.models import AccountState, OrderResult, Side, TradeIntent


class MT5SetupError(RuntimeError):
    """Raised when MT5 is unavailable or not ready for broker access."""


class MT5Broker:
    def __init__(
        self,
        config: MT5Config | None = None,
        *,
        mode: str = "mt5_demo",
        mt5_module: Any | None = None,
    ) -> None:
        self.config = config
        self.mode = mode
        self.connected = False
        self._mt5 = mt5_module

    @property
    def mt5_module(self) -> Any:
        return self._mt5

    def connect(self) -> None:
        mt5 = self._mt5
        had_initialized_session = self.connected and mt5 is not None
        self.connected = False

        if mt5 is None:
            try:
                import MetaTrader5 as mt5
            except ImportError as exc:
                self._mt5 = None
                raise MT5SetupError(
                    "MetaTrader5 Python package is required on Windows with the MT5 terminal installed."
                ) from exc

        initialize_kwargs = {}
        if self.config is not None and self.config.terminal_path is not None:
            initialize_kwargs["path"] = str(self.config.terminal_path)

        if not mt5.initialize(**initialize_kwargs):
            if had_initialized_session:
                mt5.shutdown()
            self._mt5 = None
            raise MT5SetupError(f"MT5 initialize failed: {mt5.last_error()}")

        def fail_after_initialize(message: str) -> None:
            self._mt5 = None
            mt5.shutdown()
            raise MT5SetupError(message)

        account = mt5.account_info()
        if account is None:
            fail_after_initialize(f"MT5 account_info failed: {mt5.last_error()}")

        if self.config is not None and account.login != self.config.account_number:
            fail_after_initialize(
                f"MT5 account mismatch: connected account {account.login}, expected {self.config.account_number}"
            )

        if getattr(account, "trade_allowed", True) is False:
            fail_after_initialize("MT5 account trading is not allowed.")

        terminal = mt5.terminal_info()
        if terminal is not None and getattr(terminal, "trade_allowed", True) is False:
            fail_after_initialize("MT5 terminal trading is not allowed.")

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

        mt5 = self._mt5
        config = self.config or MT5Config(
            account_number=0,
            terminal_path=None,
            server=None,
            magic=0,
            deviation_points=10,
            order_comment="forexbot",
            type_filling="return",
        )

        symbol = mt5.symbol_info(intent.symbol)
        if symbol is None:
            return OrderResult(False, None, f"MT5 symbol not found: {intent.symbol}")
        if not mt5.symbol_select(intent.symbol, True):
            return OrderResult(False, None, f"MT5 symbol is not visible: {intent.symbol}")

        tick = mt5.symbol_info_tick(intent.symbol)
        if tick is None:
            return OrderResult(False, None, f"MT5 tick not available: {intent.symbol}")

        price = tick.ask if intent.side == Side.BUY else tick.bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": intent.symbol,
            "volume": intent.volume,
            "type": mt5.ORDER_TYPE_BUY if intent.side == Side.BUY else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": intent.stop_loss,
            "tp": intent.take_profit,
            "deviation": config.deviation_points,
            "magic": config.magic,
            "comment": config.order_comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._filling_constant(mt5, config.type_filling),
        }

        success_retcodes = {mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED}
        check = mt5.order_check(request)
        check_retcode = getattr(check, "retcode", None)
        if check_retcode not in success_retcodes | {0}:
            return OrderResult(
                False,
                None,
                getattr(check, "comment", "MT5 order check failed"),
                retcode=check_retcode,
            )

        sent = mt5.order_send(request)
        send_retcode = getattr(sent, "retcode", None)
        accepted = send_retcode in success_retcodes
        return OrderResult(
            accepted,
            str(getattr(sent, "order", "")) if accepted else None,
            getattr(sent, "comment", "MT5 order sent" if accepted else "MT5 order failed"),
            retcode=send_retcode,
            deal_id=str(getattr(sent, "deal", "")) if accepted else None,
        )

    def _filling_constant(self, mt5: Any, type_filling: str) -> int:
        filling_by_name = {
            "return": mt5.ORDER_FILLING_RETURN,
            "ioc": mt5.ORDER_FILLING_IOC,
            "fok": mt5.ORDER_FILLING_FOK,
        }
        return filling_by_name.get(type_filling.lower(), mt5.ORDER_FILLING_RETURN)
