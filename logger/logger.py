import logging
import os
from datetime import datetime
from crypto_arb_finder.config import config


def configure_logger():
    # Define the logging format
    log_format = "%(asctime)s [%(levelname)s] - %(message)s - %(filename)s:%(lineno)d"
    log_file_timestamp = datetime.now().strftime("%Y%m%d")
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(
                # f"crypto_arb_finder-{log_file_timestamp}.log",
                os.path.expanduser(config.logger.logs_path)
                + f"crypto_arb_finder-{os.getpid()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
                mode="w",
            ),  # Log to a file
            logging.StreamHandler(),  # Log to console
        ],
    )


# Configure the logger when the module is imported
configure_logger()


def get_logger(name: str = None):
    return logging.getLogger(name)
