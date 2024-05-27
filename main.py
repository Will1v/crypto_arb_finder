import os, sys
from dotenv import load_dotenv
import yaml
from config import config, passwords
from logger import get_logger
from crypto_arb_finder.components.feed_handler import FeedHandler
from web_gui.app import start_web_gui
from database import db_helper

logger = get_logger(__name__)


def main():
    logger.info("Starting Crypto Arb Opportunities Finder")
    ## Initialize database
    db_helper.init_db()

    exchanges_to_monitor = ["Coinbase"]  # ["Binance", "Coinbase"]
    pairs_to_monitor = [
        ("BTC", "USD")
    ]  # [("BTC", "ETH"), ("BTC", "USD"), ("BTC", "GBP")]

    # Initialize feed handler
    feed_config = config.feed_handler
    for exchange in exchanges_to_monitor:
        for ccy_1, ccy_2 in pairs_to_monitor:
            feed_handler = FeedHandler(ccy_1, ccy_2, exchange)
            feed_handler.start()

    # Start web GUI
    # start_web_gui()


if __name__ == "__main__":
    main()
