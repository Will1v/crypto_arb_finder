import os
from dotenv import load_dotenv
import yaml

# Load environment variables from the .env file
load_dotenv('config/secrets.env')

# Load general configuration from the config.yml file
with open('config/config.yml', 'r') as file:
    config = yaml.safe_load(file)

# Import modules
from feed_handler.feed_handler import FeedHandler
# from database.db_manager import DatabaseManager
from web_gui.app import start_web_gui

def main():
    # Access configuration settings
    cc_api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    db_password = os.getenv('DB_PASSWORD')
    
    ## Initialize database
    #db_config = config['database']
    #database = DatabaseManager(db_config['host'], db_config['port'], db_config['name'], db_password)
    
    # Initialize feed handler
    feed_config = config['feed_handler']
    feed_handler = FeedHandler(feed_config['feed_url'], cc_api_key)
    feed_handler.pull_live_data('BTC', 'USD')
    
    # Start web GUI
    #start_web_gui()

if __name__ == "__main__":
    main()
