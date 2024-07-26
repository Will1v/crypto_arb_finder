import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from crypto_arb_finder.config import config, secrets
from crypto_arb_finder.logger import get_logger
import time
from typing import List, Dict


logger = get_logger(__name__)

db_params = {
    'dbname': config.database.db_name,
    'host': config.database.db_host,
    'user': config.database.db_user,
    'password': secrets.database_password,
    'port': config.database.db_port
}

db_url = f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
# Create a SQLAlchemy engine
engine = create_engine(db_url)



@st.cache_data
def get_exchanges():
    exchanges_query = "SELECT exchange FROM exchanges"
    return pd.read_sql_query(exchanges_query, engine)['exchange'].tolist()

@st.cache_data
def get_currencies_1():
    exchanges_query = "SELECT currency FROM currencies"
    return pd.read_sql_query(exchanges_query, engine)['currency'].tolist()

@st.cache_data
def get_data(time_horizon_in_hours: float):
    logger.debug("Querying data...")
    start = time.time()
    bid_ask_query = f"""
    SELECT 
    timestamp, 
    exchange,
    currency_1,
    currency_2,
    bid_q,
    bid,
    ask,
    ask_q
    FROM 
    order_book
    WHERE
        timestamp >= NOW() - INTERVAL '{time_horizon_in_hours} hours'
    ORDER BY timestamp
    """
    bid_ask_df = pd.read_sql_query(bid_ask_query, engine)
    bid_ask_df.set_index('timestamp', inplace=True)
    logger.debug(f"get_data: retrieved {bid_ask_df.size} entries")
    
    if not bid_ask_df.index.is_unique:
        bid_ask_df = bid_ask_df[~bid_ask_df.index.duplicated(keep='last')]

    # Resample and calculate the sums and averages
    def resample_group(group):
        logger.debug(f"Resampling group with keys: {group.name}")
        logger.debug(f"Group head:\n{group.head()}")
        try:
            resampled_group = group.resample('s').apply({
                'bid_q': 'sum',
                'bid': 'mean',
                'ask_q': 'sum',
                'ask': 'mean'
            }).dropna()
            
            # Add the static columns back to the resampled DataFrame
            resampled_group['exchange'] = group['exchange'].iloc[0]
            resampled_group['currency_1'] = group['currency_1'].iloc[0]
            resampled_group['currency_2'] = group['currency_2'].iloc[0]
            
            return resampled_group
        except KeyError as e:
            logger.error(f"KeyError during resampling: {e}")
            logger.debug(f"Group causing KeyError:\n{group}")
            raise e
        except Exception as e:
            logger.error(f"General error during resampling: {e}")
            logger.debug(f"Group causing error:\n{group}")
            raise e

    try:
        bid_ask_df_resampled = bid_ask_df.groupby(['exchange', 'currency_1', 'currency_2']).apply(resample_group)
        bid_ask_df_resampled.reset_index(level=['exchange', 'currency_1', 'currency_2'], drop=True, inplace=True)
    except Exception as e:
        logger.error(f"Error during resampling: {e}")
        raise e

    logger.debug(f"get_data: resampled (per second) to {bid_ask_df_resampled.size} entries")
    logger.debug(f"get_data complete in {time.time() - start:.2f} seconds")
    return bid_ask_df_resampled





def build_bid_ask_plot(current_bid_ask_df: pd.DataFrame, exchange: str, currency_1: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=current_bid_ask_df.index, y=current_bid_ask_df['bid'], mode='lines', name='Bid', line=dict(color='#A2E3C4')))
    fig.add_trace(go.Scatter(x=current_bid_ask_df.index, y=current_bid_ask_df['ask'], mode='lines', name='Ask', line=dict(color='#D90368')))
    # Set the y-axis range to start closer to the minimum bid/ask price
    min_price = min(current_bid_ask_df[['bid', 'ask']].min())
    max_price = max(current_bid_ask_df[['bid', 'ask']].max())
    fig.update_layout(
    yaxis=dict(
        range=[min_price - 1, max_price + 1],  # Adjust the range as needed
        title='Price'
    ),
    xaxis=dict(
        title='Time'
    ),
    )
    return fig

def build_spreads_plot(current_bid_ask_df: pd.DataFrame, exchange: str, currency_1: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=current_bid_ask_df.index, 
                            y=(current_bid_ask_df['ask'] - current_bid_ask_df['bid']) / (current_bid_ask_df['ask'] + current_bid_ask_df['bid']) * 2 * 10000, 
                            mode='lines', name='Bid', line=dict(color='#FFA62B')))
    # Set the y-axis range to start closer to the minimum bid/ask price
    min_price = min(current_bid_ask_df['ask'] - current_bid_ask_df['bid'])
    max_price = max(current_bid_ask_df['ask'] - current_bid_ask_df['bid'])
    fig.update_layout(
    yaxis=dict(
        range=[min_price - 1, max_price + 1],  # Adjust the range as needed
        title='Spread (in bips)'
    ),
    xaxis=dict(
        title='Time'
    ),
    
    )
    return fig


def get_arb_figures(time_horizon_in_hours: float, currency_1:str, taking_fees: Dict) -> List[go.Figure]:
    exchanges = get_exchanges()
    start = time.time()
    bid_ask_df = get_data(time_horizon_in_hours)
    logger.debug(f"Loading data which should be cached took: {time.time() - start:.2f} seconds")
    figures = []

    df_per_exchange = {}
    for exchange in exchanges:
        df_per_exchange[exchange] = bid_ask_df[(bid_ask_df['exchange'] == exchange) & (bid_ask_df['currency_1'] == currency_1)]
        logger.debug(f"{df_per_exchange[exchange].size} entries in df for {exchange}")

    for i in range(len(exchanges) - 1):
        for j in range(len(exchanges) - 1 -i):
            start = time.time()
            exchange_1 = exchanges[i]
            exchange_2 = exchanges[i + j + 1]
            total_taking_fees = taking_fees[exchange_1] + taking_fees[exchange_2]
            if df_per_exchange[exchange_1].size == 0 or df_per_exchange[exchange_2].size == 0:
                continue
            logger.debug(f"Comparing {exchange_1} vs {exchange_2}")
            df_combined = pd.concat([df_per_exchange[exchange_1], df_per_exchange[exchange_2]], axis=1, join='outer', keys=[exchange_1, exchange_2])
            # Forward fill to propagate the last valid observation forward
            df_combined = df_combined.ffill()

            # Flatten the MultiIndex columns
            df_combined.columns = ['_'.join(col).strip() for col in df_combined.columns.values]

            # Calculate the arbitrage opportunity
            df_combined[f"arbitrage_opportunity_{exchange_1}_over_{exchange_2}"] = df_combined.apply(
                lambda row: max(row[exchange_1 + '_bid'] - row[exchange_2 + '_ask'] - row[exchange_1 + '_bid'] * total_taking_fees / 100, 0) if pd.notnull(row[exchange_2 + '_ask']) else 0,
                axis=1
            )
            df_combined[f"arbitrage_opportunity_{exchange_2}_over_{exchange_1}"] = df_combined.apply(
                lambda row: max(row[exchange_2 + '_bid'] - row[exchange_1 + '_ask'] - row[exchange_2 + '_bid'] * total_taking_fees / 100, 0) if pd.notnull(row[exchange_1 + '_ask']) else 0,
                axis=1
            )
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_combined.index, 
                                    y=df_combined[f"arbitrage_opportunity_{exchange_1}_over_{exchange_2}"], 
                                    mode='lines', name=f'{exchange_1} over {exchange_2}', line=dict(color='#07553B')))
            fig.add_trace(go.Scatter(x=df_combined.index, 
                                    y=df_combined[f"arbitrage_opportunity_{exchange_2}_over_{exchange_1}"], 
                                    mode='lines', name=f'{exchange_2} over {exchange_1}', line=dict(color='#CED46A')))
            # Set the y-axis range to start closer to the minimum bid/ask price
            min_arb = 0
            max_arb = df_combined[[f"arbitrage_opportunity_{exchange_1}_over_{exchange_2}", f"arbitrage_opportunity_{exchange_2}_over_{exchange_1}"]].max(axis=1).max()
            fig.update_layout(
                yaxis=dict(
                    range=[min_arb - 1, max_arb + 1],  # Adjust the range as needed
                    title='Arbitrage opportunity'
                ),
                xaxis=dict(
                    title='Time'
                ),
                title = f"{exchange_1} over {exchange_2} arbitrage opportunities"
                )
            figures.append(fig)
            logger.debug(f"Building {exchange_1} over {exchange_2} arbitrage opportunities took {time.time() - start:.2f} seconds")
    return figures

data2 = get_data(2)
print("done")