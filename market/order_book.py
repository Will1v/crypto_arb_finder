from logger import get_logger
from datetime import datetime
import pytz
from database import db_helper
import time
import threading
import queue
from typing import Literal
import sqlite3
from sortedcontainers import SortedDict
from config import config

logger = get_logger(__name__)




class OrderBook(threading.Thread):
    def __init__(self, ccy_1: str, ccy_2: str, exchange: str) -> None:
        super().__init__()
        self.depth = config.order_book.depth
        self._ccy_1 = ccy_1
        self._ccy_2 = ccy_2
        self._exchange = exchange
        self._bid_ask_history = []
        self.last_update = datetime.now(pytz.UTC)
        self.db_queue = queue.Queue()
        self._max_db_inserts_attempts = 3

    
    def reset(self):
        logger.warning(f"Resetting order book: {self}")
        self.__init__(self._ccy_1, self._ccy_2, self.exchange)

    def init_and_start_threads(self):
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
        while self.running:
            with self.lock:
                data_batch = []
                while not self.db_queue.empty():
                    data_batch.append(self.db_queue.get())
            self.flush_to_db(data_batch)
            time.sleep(10)

    # This builds the insert query and inserts into DB
    def flush_to_db(self, data_batch):
        if data_batch:
            try:
                insert_query = f"INSERT INTO order_book (timestamp, currency_1, currency_2, bid_q, bid, ask, ask_q, exchange) VALUES "
                logger.debug(f"Flushing to DB: {insert_query}")

                values = [
                    (
                        h["event_time"].isoformat(),
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
                logger.debug(f"Attempting to insert {len(values)} values")
                for attempt in range(self._max_db_inserts_attempts):
                    try:
                        t0 = time.perf_counter()
                        db_helper.execute_many(insert_query, values)
                        logger.info(f"{len(data_batch)} entries added to DB ({(time.perf_counter() - t0) * 1000:.2f}ms)")
                        break
                    except sqlite3.OperationalError as e:
                        logger.exception(f"Sqlite3 OperationError thrown: {e}")
                        if attempt < self._max_db_inserts_attempts:
                            retry_wait = (2.7 ** (attempt + 1))
                            logger.debug(f"Will attempt new insert in {retry_wait:.2f}s")
                            time.sleep(retry_wait)
                        else:
                            logger.error(f"Insert of {len(values)} values failed after {self._max_db_inserts_attempts} attempts. Data will be missing.")

            except sqlite3.Error as e:
                logger.error(f"SQLite error: {e.args[0]}")
                logger.error("Exception occurred", exc_info=True)
            except Exception as e:
                logger.error(f"General error: {str(e)}")
                logger.error("Exception occurred", exc_info=True)
        else:
            logger.info("bid_ask_history empty, skipping...")

    # Dunder methods...
    def __str__(self) -> str:
        return f"[OrderBook] [{self.exchange}:{self._ccy_1}/{self._ccy_2}] #TODO"

class BestBidOfferOrderBook(OrderBook):
    def __init__(self, ccy_1: str, ccy_2: str, exchange: str) -> None:
        super().__init__(ccy_1=ccy_1, ccy_2=ccy_2, exchange=exchange)
        self._best_bid = None
        self._best_bid_q = None
        self._best_ask = None
        self._best_ask_q = None
        self.snapshot_complete = False
        self.init_and_start_threads()


    def set_bid_ask(self, bid: float, bid_q: float, ask: float, ask_q: float, event_time: datetime):
        self._best_bid = bid
        self._best_bid_q = bid_q
        self._best_ask = ask
        self._best_ask_q = ask_q
        self.last_update = event_time
        self.register_best_bid_offer()

    def register_best_bid_offer(self) -> None: 
            if self.snapshot_complete:
                self._bid_ask_history.append(
                    {
                        "event_time": self.last_update,
                        "bid_q": self._best_bid_q,
                        "bid": self._best_bid,
                        "ask": self._best_ask,
                        "ask_q": self._best_ask_q,
                    }
                ) 
                logger.debug(f"register_best_bid_offer: self._bid_ask_history now size {len(self._bid_ask_history)}")
            else:
                logger.warning(f"Still loading snapshot, can't register best bid offer just yet...")

    

class FullOrderBook(OrderBook):
    def __init__(self, ccy_1: str, ccy_2: str, exchange: str) -> None:
        super().__init__(ccy_1=ccy_1, ccy_2=ccy_2, exchange=exchange)
        self._bids = SortedDict(lambda x: -x)
        self._asks = SortedDict()
        self._last_best_bid = None
        self._last_best_bid_q = None
        self._last_best_ask = None
        self._last_best_ask_q = None
        self.snapshot_complete = False
        self.init_and_start_threads()

    def register_best_bid_offer(self) -> None: 
            if self.snapshot_complete:
                best_bid, best_bid_q = next(iter(self._bids.items()), (None, None))
                best_ask, best_ask_q = next(iter(self._asks.items()), (None, None))
                if (self._last_best_bid, self._last_best_bid_q, self._last_best_ask, self._last_best_ask_q) != (best_bid, best_bid_q, best_ask, best_ask_q):
                    self._bid_ask_history.append(
                        {
                            "event_time": self.last_update,
                            "bid_q": best_bid_q,
                            "bid": best_bid,
                            "ask": best_ask,
                            "ask_q": best_ask_q,
                        }
                    )
                        
                    logger.debug(f"register_best_bid_offer: self._bid_ask_history now size {len(self._bid_ask_history)}")
                    self._last_best_bid, self._last_best_bid_q, self._last_best_ask, self._last_best_ask_q = best_bid, best_bid_q, best_ask, best_ask_q
                else:
                    logger.debug("No change to BBO")
            else:
                logger.warning(f"Still loading snapshot, can't register best bid offer just yet...")
    
    def set_bid(self, bid: float, bid_q: float, event_time: datetime):
        self.register_tick(bid_ask='bid', price=bid, quantity=bid_q, event_time=event_time)

    def set_ask(self, ask: float, ask_q: float, event_time: datetime):
        self.register_tick(bid_ask='ask', price=ask, quantity=ask_q, event_time=event_time)

    def register_tick(self, bid_ask: Literal['bid', 'ask'], price: float, quantity: float, event_time: datetime):
        # If we're on a new event time, save the current BBO
        if event_time > self.last_update:
            logger.debug(f"register_tick - event_time = {event_time} newer than self.last_update = {self.last_update}")
            self.register_best_bid_offer()
            self.last_update = event_time
        # New limit or modified quantity on existing limit
        if quantity > 0:
            if bid_ask == 'bid':
                self._bids[price] = quantity
            else:
                self._asks[price] = quantity
        # Limit gone, to remove
        else:
            if bid_ask == 'bid':
                if price in self._bids:
                    del self._bids[price]
            else:
                if price in self._asks:
                    del self._asks[price] 

        while len(self._bids) > self.depth:
            self._bids.popitem()

        while len(self._asks) > self.depth:
            self._asks.popitem()

    # Dunder methods...
    def __str__(self):
        best_bid, best_bid_q = next(iter(self._bids.items()), (None, None))
        best_ask, best_ask_q = next(iter(self._asks.items()), (None, None))
        return f"[FullOrderBook] [{self.exchange}:{self._ccy_1}/{self._ccy_2}] {best_bid_q}@{best_bid} / {best_ask_q}@{best_ask}"            