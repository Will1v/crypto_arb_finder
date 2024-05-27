from crypto_arb_finder.config import config
from logger import get_logger
import os
import sqlite3

logger = get_logger(__name__)


def init_db():
    conn = get_db_connection()
    build_db_path = os.path.expanduser(config.database.build_sql_file_path)
    try:
        with open(build_db_path, "r") as file:
            sql_script = file.read()
        conn.executescript(sql_script)
        logger.info(f"Executed build DB SQL script from {build_db_path} successfully")
    except sqlite3.Error as e:
        logger.exception(f"Error executing build DB SQL script: {e}")
    except FileNotFoundError as e:
        logger.exception(f"Error: SQL file not found: {e}")


def get_db_connection():
    # Connect to DB
    conn = None
    db_file = os.path.expanduser(config.database.file_path)
    try:
        conn = sqlite3.connect(db_file)
        logger.info(f"Connected to SQLite database: {db_file}")
        return conn
    except sqlite3.Error as e:
        logger.exception(f"Error connecting to database: {e}")
    except FileNotFoundError as e:
        logger.exception(f"Error: DB file not found: {e}")
