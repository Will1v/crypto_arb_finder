CREATE TABLE IF NOT EXISTS order_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    currency_1 TEXT NOT NULL,
    currency_2 TEXT NOT NULL,
    bid_q REAL NOT NULL,
    bid REAL NOT NULL,
    ask REAL NOT NULL,
    ask_q REAL NOT NULL,
    exchange TEXT NOT NULL
);

/* TODO: change to this:

-- Create currency_pairs table
CREATE TABLE IF NOT EXISTS currency_pairs (
    currency_id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency_1 TEXT NOT NULL,
    currency_2 TEXT NOT NULL
);

-- Create exchanges table
CREATE TABLE IF NOT EXISTS exchanges (
    exchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange_name TEXT NOT NULL
);

-- Create updated order_book table with foreign keys
CREATE TABLE IF NOT EXISTS order_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    currency_id INTEGER NOT NULL,
    bid_q REAL NOT NULL,
    bid REAL NOT NULL,
    ask REAL NOT NULL,
    ask_q REAL NOT NULL,
    exchange_id INTEGER NOT NULL,
    FOREIGN KEY (currency_id) REFERENCES currency_pairs (currency_id),
    FOREIGN KEY (exchange_id) REFERENCES exchanges (exchange_id)
);
*/