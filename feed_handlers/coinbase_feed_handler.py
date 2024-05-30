from feed_handlers import FeedHandler
from config import config, secrets
from market import OrderBook
from logger import get_logger
import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
import websockets
from datetime import datetime

logger = get_logger(__name__)


class CoinbaseFeedHandler(FeedHandler):

    def __init__(self, ccy_1: str, ccy_2: str, exchange: str):
        super().__init__(ccy_1=ccy_1, ccy_2=ccy_2, exchange=exchange)
        self.feed_uri = config.feed_handler.coinbase_wss
        self.api_key = secrets.coinbase_api_key
        self.secret_key = secrets.coinbase_secret
        self.ccy_1 = ccy_1
        self.ccy_2 = ccy_2
        self.exchange = exchange
        logger.debug(f"Init FH with feed_uri = {self.feed_uri}")
        self.order_book = OrderBook(ccy_1, ccy_2, exchange)

        # Technical variables:
        self.socket_id = ""
        self.unknown_ws_types = set()
        self.reconnect_attempts = 3

    def on_message(self, ws, message):
        data = json.loads(message)
        """
        type = data["TYPE"]
        # TODO: migrate to Python 3.10 to use switch case (match)
        if type == "20":
            self.socket_id = data["SOCKET_ID"]
        elif type == "30":  # Order book update
            # TODO: are these asserts overkill?
            assert data["M"] in self.exchanges
            assert data["FSYM"] == self.ccy_1
            assert data["TSYM"] == self.ccy_2
            if "BID" in data.keys():
                self.order_book.set_bid(
                    float(data["BID"][0]["P"]),
                    float(data["BID"][0]["Q"]),
                    datetime.fromtimestamp(int(data["BID"][0]["REPORTEDNS"]) / 1e9),
                )
            if "ASK" in data.keys():
                self.order_book.set_ask(
                    float(data["ASK"][0]["P"]),
                    float(data["ASK"][0]["Q"]),
                    datetime.fromtimestamp(int(data["ASK"][0]["REPORTEDNS"]) / 1e9),
                )
        elif type not in self.unknown_ws_types:
            self.unknown_ws_types.add(type)
            """

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed: {close_status_code}, {close_msg}")
        self.running = False

    def on_open(self, ws):
        # Subscribe to the desired channels
        subscription_message = {
            "type": "subscribe",
            "product_ids": ["ETH-USD", "ETH-EUR"],
            "channels": [
                "level2",
                "heartbeat",
                {"name": "ticker", "product_ids": ["ETH-BTC", "ETH-USD"]},
            ],
        }
        logger.debug(f"Opening WS with: {subscription_message}")
        ws.send(json.dumps(subscription_message))

    def start_fh(self):
        logger.debug("Entering FH run")
        ws_url = f"{self.feed_uri}?api_key={self.cc_api_key}"

        def run_fh_ws():
            # Initialize the WebSocket
            try:
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

        fh_ws_thread = threading.Thread(target=run_fh_ws)
        logger.debug(f"Starting FH WS thread now... (FH: {self})")
        fh_ws_thread.start()
