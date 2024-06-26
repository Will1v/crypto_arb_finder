from logger import get_logger
from datetime import datetime
from database import db_helper
import time
import threading
import queue
from typing import Optional

logger = get_logger(__name__)


class OrderBook(threading.Thread):
    def __init__(self, ccy_1: str, ccy_2: str, exchange: str) -> None:
        super().__init__()
        self._ccy_1 = ccy_1
        self._ccy_2 = ccy_2
        self._exchange = exchange
        self._bid = None
        self._bid_q = None
        self._ask = None
        self._ask_q = None
        self._bid_ask_history = []
        self.db_queue = queue.Queue()

        # Multithreading management
        self.lock = threading.Lock()
        self.running = True

        # Insert order book updates thread:
        self.insertion_thread = threading.Thread(target=self.periodic_insertion)
        self.insertion_thread.daemon = True
        self.insertion_thread.start()

        # Database thread
        self.db_thread = threading.Thread(target=self.db_worker)
        self.db_thread.daemon = True
        self.db_thread.start()

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
        self.set_bid_ask(
            bid=bid, bid_q=bid_q, ask=self.ask, ask_q=self.ask_q, event_time=event_time
        )

    @property
    def ask(self):
        return self._ask

    @property
    def ask_q(self):
        return self._ask_q

    def set_ask(self, ask: float, ask_q: float, event_time: datetime):
        self.set_bid_ask(
            bid=self.bid, bid_q=self.bid_q, ask=ask, ask_q=ask_q, event_time=event_time
        )

    def set_bid_ask(
        self,
        bid: float,
        bid_q: float,
        ask: float,
        ask_q: float,
        event_time: datetime,
    ):
        logger.debug(f"set_bid_ask: bid: {bid_q}@{bid} / ask: {ask_q}@{ask}")
        with self.lock:
            if bid:
                if self._ask and bid >= self._ask:
                    logger.warning(
                        f"Crossed book: Setting bid to {bid} (>= ask {self._ask})"
                    )
                if bid < 0:
                    logger.error(f"Can't have a negative bid")
                if bid_q and bid_q < 0:
                    logger.error(f"BidQ: {bid_q} is invalid (should be >= 0)")
            self._bid = bid
            self._bid_q = bid_q
            if ask:
                if self._bid and ask <= self._bid:
                    logger.warning(
                        f"Crossed book: Setting ask to {ask} (<= bid {self._bid})"
                    )
                if ask < 0:
                    logger.error(f"ERROR: can't have a negative ask")
                if ask_q < 0:
                    logger.error(f"AskQ: {ask_q} is invalid (should be >= 0)")
            self._ask = ask
            self._ask_q = ask_q
            self._bid_ask_history.append(
                {
                    "event_time": event_time,
                    "bid_q": self._bid_q,
                    "bid": self._bid,
                    "ask": self._ask,
                    "ask_q": self._ask_q,
                }
            )
            logger.info(f"New tick: {self}")

    # This fills the queue of updates to dump in DB every 1 second
    def periodic_insertion(self):
        logger.debug(
            f"Periodic insertion thread started with ID {threading.get_ident()} ({self})"
        )
        while self.running:
            try:
                time.sleep(20)
                with self.lock:
                    # Put data in queue
                    logger.debug(f"Adding {len(self._bid_ask_history)} to queue")
                    [self.db_queue.put(entry) for entry in self._bid_ask_history]
                    self._bid_ask_history.clear()
            except Exception as e:
                logger.error(f"Error in periodic_insertion: {e}")
                break

    # This pulls data from the queue and sends it to flush_to_db for it to be inserted into DB
    def db_worker(self):
        logger.debug(f"DB worker thread started with ID: {threading.get_ident()}")
        conn = db_helper.get_db_connection()
        assert conn  # Exit if no connection to DB
        while self.running:
            with self.lock:
                data_batch = []
                while not self.db_queue.empty():
                    data_batch.append(self.db_queue.get())
            self.flush_to_db(data_batch)
            time.sleep(60)

    # This builds the insert query and inserts into DB
    def flush_to_db(self, data_batch):
        if data_batch:
            db_conn = db_helper.get_db_connection()
            insert_query = f"INSERT INTO order_book (timestamp, currency_1, currency_2, bid_q, bid, ask, ask_q, exchange) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"

            values = [
                (
                    h["event_time"],
                    self._ccy_1,
                    self._ccy_2,
                    h["bid_q"],
                    h["bid"],
                    h["ask"],
                    h["ask_q"],
                    self.exchange,
                )
                for h in data_batch
            ]
            db_conn.cursor().executemany(insert_query, values)
            db_conn.commit()
            logger.info(f"{len(data_batch)} entries added to DB")
        else:
            logger.info("bid_ask_history empty, skipping...")

    # Dunder methods...
    def __str__(self):
        return f"[OrderBook] [{self.exchange}:{self._ccy_1}/{self._ccy_2}] {self.bid_q}@{self.bid} / {self.ask_q}@{self.ask}"
