from feed_handlers import FeedHandler
from config import config, secrets
from market import OrderBook
from logger import get_logger
import traceback

# import jwt
import json
import os
import time
import websocket
import threading
from datetime import datetime

logger = get_logger(__name__)


class CoinbaseFeedHandler(FeedHandler):

    def __init__(self, ccy_1: str, ccy_2: str, exchange: str):
        super().__init__(ccy_1=ccy_1, ccy_2=ccy_2, exchange=exchange)
        self.feed_uri = config.feed_handler.coinbase_wss
        self.API_KEY = secrets.coinbase_api_key
        self.SIGNING_KEY = secrets.coinbase_signing
        self.ALGORITHM = "ES256"
        assert self.API_KEY and self.SIGNING_KEY, "API_KEY or SIGNING_KEY missing"
        self.channel = "level2"
        self.ccy_1 = ccy_1
        self.ccy_2 = ccy_2
        self.exchange = exchange
        logger.debug(f"Init FH with feed_uri = {self.feed_uri}")
        self.order_book = OrderBook(ccy_1, ccy_2, exchange)

        # Technical variables:
        self.socket_id = ""
        self.unknown_ws_types = set()
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.retry_count = 0

    def on_message(self, ws, message):
        data = json.loads(message)
        logger.debug(f"Received data on channel: {data['channel']}")
        if data.get("channel") == "l2_data":
            for event in data["events"]:
                if event["type"] == "update":
                    logger.debug(
                        f"on_message->update event for {event['product_id']}: updates = {event['updates']}"
                    )
                    bid = bid_q = ask = ask_q = None
                    new_bids = {
                        float(update["price_level"]): (
                            float(update["new_quantity"]),
                            update["event_time"],
                        )
                        for update in event["updates"]
                        if update["side"] == "bid"
                        and float(update["new_quantity"]) != 0
                    }
                    gone_bids = {
                        float(update["price_level"]): (
                            float(update["new_quantity"]),
                            update["event_time"],
                        )
                        for update in event["updates"]
                        if update["side"] == "bid"
                        and float(update["new_quantity"]) == 0
                    }
                    new_asks = {
                        float(update["price_level"]): (
                            float(update["new_quantity"]),
                            update["event_time"],
                        )
                        for update in event["updates"]
                        if update["side"] == "offer"
                        and float(update["new_quantity"]) != 0
                    }
                    gone_asks = {
                        float(update["price_level"]): (
                            float(update["new_quantity"]),
                            update["event_time"],
                        )
                        for update in event["updates"]
                        if update["side"] == "offer"
                        and float(update["new_quantity"]) == 0
                    }

                    logger.debug(
                        f"new_bids = {new_bids}, gone_bids = {gone_bids}, new_asks = {new_asks}, gone_asks = {gone_asks}"
                    )

                    if gone_bids and self.order_book.bid in gone_bids.keys():
                        # Best bid gone
                        bid = bid_q = None
                    if new_bids and (
                        not self.order_book.bid
                        or self.order_book.bid <= max(new_bids.keys())
                    ):
                        # New best bid
                        bid = max(new_bids.keys())
                        bid_q = new_bids[bid][0]

                    if gone_asks and self.order_book.ask in gone_asks.keys():
                        # Best bid gone
                        ask = ask_q = 0
                    if new_asks and (
                        not self.order_book.ask
                        or self.order_book.ask >= min(new_asks.keys())
                    ):
                        # New best bid
                        ask = min(new_asks.keys())
                        ask_q = new_asks[ask][0]

                    tick_timestamp = event["updates"][0]["event_time"]
                    logger.debug(f"tick_timestamp = {tick_timestamp}")
                    self.order_book.set_bid_ask(
                        bid=bid,
                        bid_q=bid_q,
                        ask=ask,
                        ask_q=ask_q,
                        event_time=tick_timestamp,
                    )
        else:
            logger.debug(f"Non l2_data message received: {data}")

    def on_open(self, ws):
        # Subscribe to the desired channels
        try:
            subscription_message = {
                "type": "subscribe",
                "channel": self.channel,
                "product_ids": [f"{self.ccy_1}-{self.ccy_2}"],
            }
            logger.debug(f"Opening WS with: {subscription_message}")
            signed_message = self.sign_with_jwt(
                subscription_message, self.channel, ["ETH-USD", "ETH-EUR"]
            )
            ws.send(json.dumps(subscription_message))
        except Exception as e:
            error_details = "".join(
                traceback.format_exception(type(e), e, e.__traceback__)
            )
            logger.exception(f"Error during WebSocket open: {error_details}")

    def on_error(self, ws, error):
        if isinstance(error, Exception):
            error_details = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            logger.exception(f"WebSocket error: {error_details}")
        else:
            logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed: {close_status_code}, {close_msg}")
        self.running = False

    def retry_connection(self):
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            logger.info(f"Retrying connection in {self.retry_delay} seconds...")
            time.sleep(self.retry_delay)
            self.run()
        else:
            logger.error("Max retries exceeded. Could not connect to WebSocket.")
            self.running = False

    def stop_fh(self):
        self.running = False
        if self.ws:
            self.ws.close()

    def sign_with_jwt(self, message, channel, products=[]):
        # Not implemented, not needed for now.
        return message

    def start_fh(self):
        logger.debug("Entering FH run")
        ws_url = self.feed_uri

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
