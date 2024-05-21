## Project progress

- [ ] Preliminary work
   - [x] Decide on crypto API:  <a href="https://min-api.cryptocompare.com/" target="_blank">Crypto Compare</a>
   - [x] Decide on database: sqlite3
- [ ] Feed handler
- [ ] Web GUI

## Configuration Setup

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

