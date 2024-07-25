from crypto_arb_finder.config import config, secrets
from logger import get_logger
import os
import psycopg2
from threading import Lock, Thread

logger = get_logger(__name__)

class Database:

    _instance = None
    _lock = Lock()

    # Insuring database is a singleton
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    logger.debug("database instance has not be init yet, creating it now")
                    cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.conn = psycopg2.connect(database=config.database.db_name,
                            host=config.database.db_host,
                            user=config.database.db_user,
                            password=secrets.database_password,
                            port=config.database.db_port)
        self.conn.autocommit = True

        build_db_path = os.path.expanduser(config.database.build_sql_file_path)
        try:
            with open(build_db_path, "r") as file:
                sql_script = file.read()
            with self.conn.cursor() as cursor:
                cursor.execute(sql_script)
            logger.info(f"Executed build DB SQL script from {build_db_path} successfully") 
        except FileNotFoundError as e:
            logger.exception(f"Error: SQL file not found: {e}")


database = Database()

def execute_many(query: str, args: list):
    with database.conn.cursor() as cursor:
        mogrified_args = ','.join(cursor.mogrify("(" + ", ".join(["%s"] * len(args[0])) + ")", i).decode("utf-8") for i in args)
        cursor.execute(query + mogrified_args)

def execute(query:str):
    with database.conn.cursor() as cursor:
        cursor.execute(query)

