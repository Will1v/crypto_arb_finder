import os
from dotenv import load_dotenv
import yaml
from config import config, passwords
from logger import get_logger
from crypto_arb_finder.components.feed_handler import FeedHandler
from web_gui.app import start_web_gui

logger = get_logger(__name__)


def main():
    logger.info("Starting Crypto Arb Opportunities Finder")
    ## Initialize database
    # db_config = config['database']
    # database = DatabaseManager(db_config['host'], db_config['port'], db_config['name'], db_password)

    exchanges_to_monitor = ["Binance", "Coinbase"]
    pairs_to_monitor = [("BTC", "ETH"), ("BTC", "USD"), ("BTC", "GBP")]

    # Initialize feed handler
    feed_config = config.feed_handler
    for exchange in exchanges_to_monitor:
        for ccy_1, ccy_2 in pairs_to_monitor:
            feed_handler = FeedHandler(ccy_1, ccy_2, exchange)
            feed_handler.pull_live_data()

    # Start web GUI
    # start_web_gui()


if __name__ == "__main__":
    main()
