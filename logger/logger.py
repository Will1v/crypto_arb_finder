import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime
from crypto_arb_finder.config import config


def configure_logger():
    # Define the logging format
    log_format = "%(asctime)s.%(msecs)03d [%(levelname)s] - %(message)s - %(filename)s:%(lineno)d"

    # TimedRotatingFileHandler to rotates logs every hour
    log_file_handler = TimedRotatingFileHandler(
        os.path.expanduser(config.logger.logs_path) + "crypto_arb_finder.log",
        when="H",  # Rotate logs every hour
        interval=1,  # The interval to rotate logs
        # backupCount=24  # Number of backup files to keep
    )
    log_file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))

    # Create a StreamHandler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[log_file_handler, console_handler],
    )

"""    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(
                os.path.expanduser(config.logger.logs_path)
                + f"crypto_arb_finder-{os.getpid()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
                mode="w",
            ),  
            logging.StreamHandler(),  # Log to console
        ],
    )"""


# Configure the logger when the module is imported
configure_logger()


def get_logger(name: str = None):
    return logging.getLogger(name)
