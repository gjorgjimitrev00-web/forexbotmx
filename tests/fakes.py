from types import SimpleNamespace


class FakeMT5:
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_RETURN = 2
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_FOK = 0
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008

    def __init__(self) -> None:
        self.sent_requests = []
        self.checked_requests = []
        self.initialize_result = True
        self.account = SimpleNamespace(login=12345678, equity=10000.0, balance=10000.0, trade_allowed=True)
        self.terminal = SimpleNamespace(trade_allowed=True)
        self.tick = SimpleNamespace(bid=1.1048, ask=1.1050)
        self.symbol = SimpleNamespace(name="EURUSD", visible=True, point=0.0001)
        self.check_result = SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, comment="check ok")
        self.send_result = SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=111, deal=222, comment="done")

    def initialize(self, *args, **kwargs):
        return self.initialize_result

    def last_error(self):
        return (1, "fake error")

    def account_info(self):
        return self.account

    def terminal_info(self):
        return self.terminal

    def positions_get(self):
        return ()

    def symbol_info(self, symbol):
        return self.symbol if symbol == "EURUSD" else None

    def symbol_select(self, symbol, selected):
        return symbol == "EURUSD" and selected

    def symbol_info_tick(self, symbol):
        return self.tick if symbol == "EURUSD" else None

    def order_check(self, request):
        self.checked_requests.append(request)
        return self.check_result

    def order_send(self, request):
        self.sent_requests.append(request)
        return self.send_result
