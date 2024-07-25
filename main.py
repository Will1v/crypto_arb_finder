from dotenv import load_dotenv
from logger import get_logger
from feed_handlers import KrakenFeedHandler, CoinbaseFeedHandler
from database import db_helper

logger = get_logger(__name__)


def main():
    logger.info("Starting Crypto Arb Opportunities Finder")

    coins = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'XRP', 'USDC', 'DOGE', 'TON', 'ADA']
    exchanges = {'Coinbase': CoinbaseFeedHandler, 'Kraken': KrakenFeedHandler}

    init_coins_query = f"""
        INSERT INTO currencies (currency)
        VALUES
            ('{"'), ('".join([c for c in coins])}')
        ON CONFLICT (currency) DO NOTHING;
    """

    init_exchanges_query = f"""
        INSERT INTO exchanges (exchange)
        VALUES
            ('{"'), ('".join([e for e in exchanges.keys()])}')
        ON CONFLICT (exchange) DO NOTHING;
    """

    db_helper.execute(init_coins_query)
    db_helper.execute(init_exchanges_query)

    feed_handlers = []
    for coin in coins:
        for fh in exchanges.values():
            feed_handlers.append(fh(coin, "USD"))
            feed_handlers.append(fh(coin, "USD"))
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
