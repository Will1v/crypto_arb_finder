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


# Working notes

## BBO order book vs Full order book

Initially used Kraken's BBO feed vs Coinbase's full order book feed. Kraken's BBO feed looks very illiquid, so will try to use a full order book instead.
![image](https://github.com/user-attachments/assets/8acb6ea0-5056-4c56-871b-54da4a93e2b5)

Full order book actually looks similar. Couple of observations:
- Displaying the spreads does show that for BTC/USD Coinbase is one a 1ct spread whereas Kraken is on 10ct which would explain more stable prices
- It seems like Kraken's feed broadcasts "stable" order book (ie first limit will go straigth from 639001.1/639001.2 to 639002.3/639002.4, keeping its spread to 10ct most of the time) while Coinbase would be more realistic (eg going 639001.1/639001.2 -> 639001.1/639002.4 -> 639002.3/639002.4, therefore having the spread going 10ct -> 130ct -> 10ct)

![image](https://github.com/user-attachments/assets/7264d615-3bfa-4815-b020-091c124102a2)

## Database issues

- Grafana seems to be locking the DB a lot when pulling data to plot the charts
- It's also extremely slow (half a minute for each plot over 15 minutes sliding windows)
- New retry mechanism helps with the data loss but the dashboard performance is terrible. Will need to look into migrating to Postgresql


## Some results

At first glance, there are non negligeable discrepencies between Coinbase and Kraken on BTC and ETH - at least on the first limit, which is what is displayed here - but not enough once you factor in trading fees. 

![image](https://github.com/user-attachments/assets/8af95b92-4dce-484d-9937-3ec5b935fbc7)
