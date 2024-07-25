import threading
import websocket
from abc import ABC, abstractmethod
from crypto_arb_finder.market.order_book import OrderBook
from logger import get_logger
import time

logger = get_logger(__name__)


class FeedHandler(ABC):

    def __init__(self, ccy_1: str, ccy_2: str, exchange: str):

        self.ccy_1 = ccy_1
        self.ccy_2 = ccy_2
        self.exchange = exchange
        self.order_book = OrderBook(ccy_1, ccy_2, exchange)

        # Technical variables:
        self.socket_id = ""
        self.unknown_ws_types = set()
        self.reconnect_attempts = 3

    @abstractmethod
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        pass

    @abstractmethod
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        pass

    @abstractmethod
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closing"""
        pass

    @abstractmethod
    def on_open(self, ws):
        """Handle WebSocket opening"""
        pass

    def start_fh(self):
        logger.debug("Entering FH run")
        ws_url = self.feed_uri

        def run_fh_ws():
            logger.debug(f"Now {threading.active_count()} active threads")
            # Initialize the WebSocket
            while True:
                try:
                    self.order_book.reset()
                    # websocket.enableTrace(True)
                    ws = websocket.WebSocketApp(
                        ws_url,
                        on_open=self.on_open,
                        on_message=self.on_message,
                        on_error=self.on_error,
                        on_close=self.on_close,
                    )
                    # Run the WebSocket
                    logger.debug("starting ws.run_forever() now...")
                    ws.run_forever()
                except Exception as e:
                    logger.exception(f"Exception occurred: {e}")
                    if ws:
                        ws.close()
                logger.debug("Sleeping 5s before attempting a reconnection")
                time.sleep(5)

        fh_ws_thread = threading.Thread(target=run_fh_ws)
        logger.debug(f"Starting FH WS thread now... (FH: {self})")
        fh_ws_thread.start()

    # Dunder methods...
    def __str__(self):
        return f"[FeedHandler] {self.exchange}: {self.ccy_1}/{self.ccy_2}"
