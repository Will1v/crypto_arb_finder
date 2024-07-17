## Project progress

- [x] Preliminary work
   - [x] Decide on crypto API:  <a href="https://min-api.cryptocompare.com/" target="_blank">Crypto Compare</a>
   - [x] Decide on database: sqlite3
- [ ] Feed handler
   - [x] Store market data to DB
      - [x] For one exchange
      - [ ] For multiple exchanges
         - [x] Kraken
         - [x] Coinbase
         - [ ] Cex.io
   - [ ] Spot arbitrage opportunities
- [ ] Web GUI

# Getting started
## Installing required modules

Ensure `pip` is installed, then run:
``` sh
pip install -r requirements.txt
```

## Configuration files

1. Copy the template files to create your actual configuration files:

   ```sh
   cp config/secrets.template.env config/secrets.env
   cp config/config.template.yml config/config.yml
   ```

2. Set up the custom files 

    * secrets.env
        * API_KEY: API key for CryptoCompare. Get one for free at: https://min-api.cryptocompare.com/pricing
        * DB_PASSWORD: password for you database
    
    * config.yml
    TODO

## Python Path

Ensure the directory in which the code lives is in your Python Path.
For example, add:
``` sh
export PYTHONPATH="<path/to/project>"
```
to your `.bash_profile`

## Database

Ensure you have at least a placeholder file for the sqlite3 database.
For example, run:
``` sh
touch database/crypto_arb_finder.sqlite3
```
(NB: make sure this matches what you've defined in `config/config.yaml`)


# Notes

Initially used Kraken's BBO feed vs Coinbase's full order book feed. Kraken's BBO feed looks very illiquid, so will try to use a full order book instead.
![image](https://github.com/user-attachments/assets/8acb6ea0-5056-4c56-871b-54da4a93e2b5)
