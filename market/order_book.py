from logger import get_logger
from datetime import datetime
from database import db_helper
import time
import threading


logger = get_logger(__name__)


class OrderBook(threading.Thread):
    def __init__(self, ccy_1: str, ccy_2: str, exchange: str) -> None:
        self._ccy_1 = ccy_1
        self._ccy_2 = ccy_2
        self._exchange = exchange
        self._bid = 0
        self._bid_q = 0
        self._ask = 0
        self._ask_q = 0
        self._bid_ask_history = []

        self.db_conn = db_helper.get_db_connection()
        assert self.db_conn  # Exit if no connection to DB

        # Multithreading management
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.running = True

        # Insert order book updates thread:
        self.insertion_thread = threading.Thread(target=self.periodic_insertion)
        self.insertion_thread.start()

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
        logger.debug("Setting Bid")
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
        logger.debug(f"bid_ask_history updated, now size: {len(self._bid_ask_history)}")

    @property
    def ask(self):
        return self._ask

    @property
    def ask_q(self):
        return self._ask_q

    def set_ask(self, ask: float, ask_q: float, event_time: datetime):
        logger.debug("Setting Ask")
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
        logger.debug(f"bid_ask_history updated, now size: {len(self._bid_ask_history)}")

    def periodic_insertion(self):
        logger.debug(
            f"Starting thread to dump order book updates (if any) in DB (Order book: {self._ccy_1}/{self._ccy_2} on {self.exchange})"
        )
        while self.running:
            logger.debug(f"Flushing: {self._bid_ask_history}")
            time.sleep(1)
            with self.lock:
                self.flush_to_db()
        logger.debug(
            f"Exiting periodic_insertion thread. (self.running = {self.running})"
        )

    def flush_to_db(self):
        logger.debug("flush_to_db called")
        if self._bid_ask_history:
            insert_query = "INSERT INTO order_book (timestamp, currency_1, currency_2, bid_q, bid, ask, ask_q, exchange) VALUES ("
            for h in self._bid_ask_history:
                insert_query += f"({h.event_time}, {self._ccy_1}, {self._ccy_2}, {h.bid_q}, {h.bid}, {h.ask}, {ask_q}, {self.exchange}), "
            insert_query += ");"
            logger.debug(f"flush_to_db running: {insert_query}")
            self.db_conn.cursor().execute(insert_query)
            self.db_conn.commit()
            self._bid_ask_history = []
        else:
            logger.debug("bid_ask_history empty, skipping...")
