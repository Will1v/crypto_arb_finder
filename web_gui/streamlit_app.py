import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
st.set_page_config(layout="wide")

from datetime import datetime
from crypto_arb_finder.config import config, secrets
import time
from crypto_arb_finder.logger import get_logger
from streamlit_helper import get_exchanges, get_currencies_1, get_data, build_bid_ask_plot, build_spreads_plot, get_arb_figures


logger = get_logger(__name__)


page_load_start = time.time()

time_horizon = config.web_gui.time_horizon_in_hours
time_horizon = 2
logger.debug(f"Time horizon: {time_horizon} hours")

start = time.time()
exchanges = get_exchanges()
start = time.time()
currencies_1 = get_currencies_1()
start = time.time()
st.toast(f"Fetching data...")
bid_ask_df = get_data(time_horizon_in_hours=time_horizon)
st.toast("Data retrieved.")
logger.debug(f"get_data() took {time.time() - start:.2f}")



currency_1 = st.sidebar.selectbox("Coin to display:", currencies_1)
currency_2 = 'USD'

taking_fees = {}
default_taking_fees = {
     'Coinbase': 0.40,
     'Kraken': 0.40
}
for exchange in exchanges:
     taking_fees[exchange] = st.sidebar.number_input(f"Taking fee for {exchange} (%):", min_value=0.0, max_value=100.0, step=0.01, format="%.2f", value=default_taking_fees[exchange])

arb_container = st.container()
exchanges_container = st.container()

with arb_container:
    st.subheader("Arbitrage opportunities")

    for fig in get_arb_figures(time_horizon_in_hours=time_horizon, currency_1=currency_1, taking_fees=taking_fees):
         st.plotly_chart(fig)

with exchanges_container:
    st.subheader("Breakdown per exchange")
    for exchange in exchanges:
         start = time.time()

         col1, col2, col3 = st.columns(3)
         columns = [col1, col2, col3]

         current_bid_ask_df = bid_ask_df[(bid_ask_df['exchange'] == exchange) & (bid_ask_df['currency_1'] == currency_1) & (bid_ask_df['currency_2'] == currency_2)]
         if current_bid_ask_df.size == 0:
              st.warning(f"No data found for {currency_1}/USD on {exchange} over the past {time_horizon} hours.")
              continue

         with columns[0]:
              # Display the plotly figure in Streamlit
              st.markdown(f"###### {exchange} - {currency_1}/USD - Bid/Ask")
              st.plotly_chart(build_bid_ask_plot(current_bid_ask_df,  exchange, currency_1))
         with columns[1]:
              # Display the plotly figure in Streamlit
              volumes_df = pd.DataFrame({
                   'bid_q': current_bid_ask_df['bid_q'],
                   'ask_q': -current_bid_ask_df['ask_q']
              })
              st.markdown(f"###### {exchange} - {currency_1}/USD - Volume Spread")
              st.bar_chart(volumes_df, color=['#A2E3C4', '#D90368'])
               
         with columns[2]:
              # Display the plotly figure in Streamlit
              st.markdown(f"###### {exchange} - {currency_1}/USD - Spreads")
              st.plotly_chart(build_spreads_plot(current_bid_ask_df,  exchange, currency_1))
              
         logger.debug(f"Plotting {exchange} took {time.time() - start:.2f}")

st.markdown(f"<p class='footnote'>Page generated in {time.time() - page_load_start:.2f} seconds.</p>", unsafe_allow_html=True)
