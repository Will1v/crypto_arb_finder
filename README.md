## Project progress

- [x] Preliminary work
   - [x] Decide on crypto API:  <a href="https://min-api.cryptocompare.com/" target="_blank">Crypto Compare</a>
   - [x] Decide on database: PostgreSQL
- [X] Feed handler
   - [x] Store market data to DB
      - [x] For one exchange
      - [X] For multiple exchanges
         - [x] Kraken
         - [x] Coinbase
         - [ ] Cex.io
   - [X] Spot arbitrage opportunities
- [X] Web GUI

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

Replace `to_be_set` with appropriate values

 - secrets.env
     - COINBASE_API_KEY: Coinbase API key
     - COINBASE_SIGNING_KEY: Coinbase signing key
     - DB_PASSWORD: password for you database
 
 - config.yaml
    - database: specify DB name, user, host, port (typically `5432`) and the path to the build script (typically `crypto_arb_finder/database/build_database.sql`)
    - feed_handler: specify the various exchanges' wss addresses
    - order_book: specify depth
    - logger: logs path
    - web_gui: specify the maximum time horizon you want to pull data over (in hours)

## Python Path

Ensure the directory in which the code lives is in your Python Path.
For example, add:
``` sh
export PYTHONPATH="<path/to/project>"
```
to your `.bash_profile`

## Database

Install Postgresql (I used v11.22).

## Running the app

### Backend

I run the feed handlers and DB on a Raspberry Pi 4.

`nohup python /home/will1v/crypto_arb_finder/main.py > /dev/null 2>&1 &`

*NB:* if working with limited resources as you would on a Raspberry Pi, make sure you disable DEBUG logs or backup/delete log files. You might want to periodically drop some of the database's older data.

### Web GUI

Built with streamlit (see streamlit.io). To launch the engine, run:
`streamlit run <path_to_project>/crypto_arb_finder/web_gui/streamlit_app.py`

If running with DEBUG logs, you'll want to add `--server.fileWatcherType=none` to the above command.

# Working notes

## BBO order book vs Full order book

Initially used Kraken's BBO feed vs Coinbase's full order book feed. Kraken's BBO feed looks very illiquid, so will try to use a full order book instead.
![image](https://github.com/user-attachments/assets/8acb6ea0-5056-4c56-871b-54da4a93e2b5)

Full order book actually looks similar. Couple of observations:
- Displaying the spreads does show that for BTC/USD Coinbase is one a 1ct spread whereas Kraken is on 10ct which would explain more stable prices
- It seems like Kraken's feed broadcasts "stable" order book (ie first limit will go straigth from 639001.1/639001.2 to 639002.3/639002.4, keeping its spread to 10ct most of the time) while Coinbase would be more realistic (eg going 639001.1/639001.2 -> 639001.1/639002.4 -> 639002.3/639002.4, therefore having the spread going 10ct -> 130ct -> 10ct)

![image](https://github.com/user-attachments/assets/7264d615-3bfa-4815-b020-091c124102a2)

## Final verdict

- After building the web GUI using streamlit (see streamlit.io), here's what you would see with default fees on both side. On quiet markets there wouldn't typically be any opportunities:
![image](https://github.com/user-attachments/assets/102d78e6-9f08-417d-8c37-3ea73a223e10)

- With better fees you start seeing opportunities. For instance, this screenshot on Solana if you were in the $1m+ 30-days trading tier on both exchanges you had the first leg as a passive order, subseauently aggressing on the second leg (ie paying 8bps on Coinbase, 10bps on Kraken):
![image](https://github.com/user-attachments/assets/d9f8e8a8-5858-4304-a552-f4c3788f1dce)



- Setting all fees to 0 shows the raw discrepancies between the exchanges (here on BTC):
![image](https://github.com/user-attachments/assets/1a0a9254-5e7b-4413-84fb-a9371363dec8)

## Database issues

### Using Sqlite3
- Grafana seems to be locking the DB a lot when pulling data to plot the charts
- It's also extremely slow (half a minute for each plot over 15 minutes sliding windows)
- New retry mechanism helps with the data loss but the dashboard performance is terrible. **Have migrated to Postgresql**

## Performance considerations

The sheer amount of data pulled makes the dashboard very slow. I've had to:
- Reduce the timeframe of data pulled into the Pandas dataframes
- Resample the data to one data point per second

For context, over the past 24h (quiet markets), the average count of updates varied from 8 to 30 per second:
``` sql
SELECT
	exchange,
	currency_1,
	ROUND(AVG(count)) as average_count
FROM
(
	SELECT 
		exchange, 
		currency_1, 
		date_trunc('second', timestamp) AS second, 
		COUNT(*) AS count
	FROM 
		order_book
	WHERE 
		timestamp >= NOW() - INTERVAL '24 hours'
	GROUP BY 
		exchange, 
		currency_1, 
		second
) AS count_per_second
GROUP BY
	count_per_second.exchange,
	count_per_second.currency_1
ORDER BY
	3, 2, 1;
 exchange | currency_1 | average_count
----------+------------+---------------
 Coinbase | ADA        |             8
 Kraken   | ETH        |             8
 Kraken   | SOL        |             8
 Kraken   | BTC        |             9
 Coinbase | XRP        |             9
 Kraken   | ADA        |            11
 Coinbase | SOL        |            11
 Kraken   | XRP        |            17
 Coinbase | ETH        |            28
 Coinbase | BTC        |            30
(10 rows)
```


This version is focused on exploring/back testing and storing data. 

For a live trading implementation, having the database intermediate wouldn't be suitable. I would need to compare the live order books in memory, perhaps using something like Redis, and react to signals on the fly.
