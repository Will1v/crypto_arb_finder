from logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


class OrderBook:
    def __init__(
        self,
        ticker: str,
        exchange: str,
        bid: float,
        bid_q: float,
        ask: float,
        ask_q: float,
    ) -> None:
        self._ticker = ticker
        self._exchange = exchange
        self._bid = bid
        self._bid_q = bid_q
        self._ask = ask
        self._ask_q = ask_q
        self._bid_ask_history = []

    @property
    def ticker(self):
        return self._ticker

    @property
    def exchange(self):
        return self._exchange

    @property
    def bid(self):
        return self._bid

    @property
    def bid_q(self):
        return self._bid_q

    def set_bid(self, bid: float, bid_q: float, event_time: datetime):
        if bid >= self._ask:
            logger.warn(f"WARNING: setting bid to {bid} (>= ask {self._ask})")
        if bid < 0:
            logger.error(f"ERROR: can't have a negative bid")
        if bid_q < 0:
            logger.error(f"BidQ: {bid_q} is invalid (should be >=)")
        self._bid = bid
        self._bid_q = bid_q
        self._bid_ask_history.append(
            (event_time, self._bid_q, self._bid, self._ask, self._ask_q)
        )

    @property
    def ask(self):
        return self._ask

    @property
    def ask_q(self):
        return self._ask_q

    def set_ask(self, ask: float, ask_q: float, event_time: datetime):
        if ask <= self._bid:
            logger.warn(f"WARNING: setting ask to {ask} (<= bid {self._bid})")
        if ask < 0:
            logger.error(f"ERROR: can't have a negative ask")
        if ask_q < 0:
            logger.error(f"AskQ: {ask_q} is invalid (should be >=)")
        self._ask = ask
        self._ask_q = ask_q
        self._bid_ask_history.append(
            (event_time, self._bid_q, self._bid, self._ask, self._ask_q)
        )
