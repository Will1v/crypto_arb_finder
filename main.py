import os, sys, time
from dotenv import load_dotenv
import yaml
from config import config
from logger import get_logger
from feed_handlers import KrakenFeedHandler, CoinbaseFeedHandler
from web_gui.app import start_web_gui
from database import db_helper

logger = get_logger(__name__)


def main():
    logger.info("Starting Crypto Arb Opportunities Finder")

    # TODO: rework this
    feed_handlers = []
    feed_handlers.append(CoinbaseFeedHandler("BTC", "USD"))
    feed_handlers.append(KrakenFeedHandler("BTC", "USD"))
    feed_handlers.append(CoinbaseFeedHandler("ETH", "USD"))
    feed_handlers.append(KrakenFeedHandler("ETH", "USD"))
    try:
        for feed_handler in feed_handlers:
            feed_handler.start_fh()
    except KeyboardInterrupt:
        logger.info(f"KeyboardInterrupt: Stopping FH [{feed_handler}]")
        feed_handler.stop_fh()
        logger.info(f"Feed handler [{feed_handler}] stopped")

    # Start web GUI
    # start_web_gui()


if __name__ == "__main__":
    main()
