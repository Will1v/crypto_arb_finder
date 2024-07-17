from feed_handlers import FeedHandler
from config import config, secrets
from market import BestBidOfferOrderBook
from logger import get_logger
import json
import threading
import websocket
from datetime import datetime

logger = get_logger(__name__)


class KrakenFeedHandler(FeedHandler):

    def __init__(self, ccy_1: str, ccy_2: str):
        exchange = "Kraken"
        super().__init__(ccy_1=ccy_1, ccy_2=ccy_2, exchange=exchange)
        self.feed_uri = config.feed_handler.kraken_wss
        self.ccy_1 = ccy_1
        self.ccy_2 = ccy_2
        self.exchange = exchange
        logger.debug(f"Init FH with feed_uri = {self.feed_uri}")
        self.order_book = BestBidOfferOrderBook(ccy_1, ccy_2, self.exchange)

        # Technical variables:
        self.socket_id = ""
        self.unknown_ws_types = set()
        self.reconnect_attempts = 3

    def on_message(self, ws, message):
        try:
            response = json.loads(message)
            if (
                response.get("channel") == "ticker"
                and response.get("type") == "update"
                and "data" in response
            ):
                data = response["data"][0]
                assert (
                    data["symbol"] == f"{self.ccy_1}/{self.ccy_2}"
                ), f"response[data][symbol] = {data['symbol']} which does not match self.ccy_1/self.ccy_2 = {self.ccy_1}/{self.ccy_2}"
                # Note: Kraken's API isn't great in that it doesn't provide a timestamp for the update. This means we could have inacurate timestamps if the program starts lagging...
                self.order_book.set_bid_ask(
                    data["bid"],
                    data["bid_qty"],
                    data["ask"],
                    data["ask_qty"],
                    datetime.utcnow(),
                )
            else:
                logger.debug(f"Received non data message: {response}")

        except Exception as e:
            logger.exception(f"Error processing message: {e}")

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed: {close_status_code}, {close_msg}")
        self.running = False

    def on_open(self, ws):
        # Subscribe to the desired channels
        subscription_message = {
            "method": "subscribe",
            "params": {
                "channel": "ticker",
                "symbol": [f"{self.ccy_1}/{self.ccy_2}"],
                "event_trigger": "bbo",
                "snapshot": False,
            },
        }
        logger.debug(f"Opening WS with: {subscription_message}")
        ws.send(json.dumps(subscription_message))

    def start_fh(self):
        logger.debug("Entering FH run")
        ws_url = f"{self.feed_uri}"

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
