import streamlit as st
import pandas as pd
import math
from pathlib import Path
import yfinance as yf
import backtrader as bt
from datetime import datetime
import matplotlib.pyplot as plt

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='My Share Trading Strategies dashboard',
    page_icon=':chart_with_upwards_trend:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def fetch_stock_data(ticker, start_date, end_date):
    """Fetch stock data from yfinance for a given ticker."""
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    
    return stock_data

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

gdp_df = get_gdp_data()



# Define your strategy class (example)
class MovingAverageCross(bt.Strategy):
    # Define parameters and methods for your strategy
    def __init__(self):
        self.ma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=15)
        self.ma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=30)

    def next(self):
        current_date = self.data.datetime.date(0)  # Get the current date
        current_close = self.data.close[0]         # Get the current close price

        if 'messages' not in st.session_state:
            st.session_state.messages = []  # Initialize the messages list



        if self.ma_short[0] > self.ma_long[0]:
            if not self.position:
                 
                message = f"BUY on {current_date} at {current_close}"
                st.session_state.messages.append(message)
                self.buy()  # Buy signal
        elif self.ma_short[0] < self.ma_long[0]:
            if self.position:
                message = f"SELL on {current_date} at {current_close}"
                st.session_state.messages.append(message)
                self.sell()  # Sell signal


# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :chart_with_upwards_trend: My Share Trading Strategies

This trading strategy is a moving average cross over strategy. If the share is in a sidewards trend, this strategy is not recommended.
'''

# Add some spacing
''
''


#start_date, end_date = st.slider(
#    'Which dates are you interested in?',
#    min_value=pd.to_datetime('2024-01-01'),
#    max_value=pd.to_datetime(datetime.today().date()), 
#    value=(pd.to_datetime('2024-01-01'), pd.to_datetime(datetime.today().date())) 
#)



selected_share = st.selectbox(
    'Which share would you like to view?',
    ['BBVA.MC', 'SAN.MC', 'ANE.MC', 'MEL.MC', 'REP.MC', 'OFX.AX', 'XC02.AX', 'PEN.AX', 'RBTZ.AX', 'WMI.AX', 'WAR.AX' ,'AGL.AX', 'NUF.AX', 'WWI.AX', 'PPT.AX', 'FLC.AX','CSL.AX', 'CRYP.AX', 'PE1.AX', 'PCX.AX', 'MQAE.AX', 'CSC.AX', 'RIO.AX'])

if not selected_share:
    st.warning("Select one share")

start_date = st.date_input("Start Date", value=pd.to_datetime('2024-01-01'))
end_date = st.date_input("End Date", value=datetime.today())

''




if start_date and end_date and start_date < end_date:
    # Add a button to extract the data
    if st.button('Get Trading Strategy'):
        if selected_share:

            st.header(f'Trading strategy for {selected_share}', divider='gray')
            stock_data = fetch_stock_data(selected_share, start_date, end_date)
            

            # Check if stock_data is empty
            if stock_data.empty:
                st.warning("No data found for the selected ticker and date range.")
            else:
                # Convert the fetched data to a CSV format for Backtrader
                stock_data.reset_index(inplace=True)  # Reset index to have a proper datetime column

                # Save to a temporary CSV file
                temp_file_name = 'temp_stock_data.csv'
                stock_data.to_csv(temp_file_name, index=False)

                # Load data into Backtrader
                data = bt.feeds.GenericCSVData(
                    dataname=temp_file_name,
                    dtformat='%Y-%m-%d',
                    openinterest=-1  # Assuming there's no open interest data
                )

                # Create a cerebro engine instance
                cerebro = bt.Cerebro()

                # Add the data feed to cerebro
                cerebro.adddata(data)

                # Add the strategy to cerebro
                cerebro.addstrategy(MovingAverageCross)

                # Run the backtest
                cerebro.run()

                if 'messages' in st.session_state and st.session_state.messages:
                    with st.sidebar:
                        st.header('Trade Signals')
                        for msg in st.session_state.messages:
                            st.write(msg)  # Display each message in the sidebar
                

                # Create a plot and display it in Streamlit
                figs = cerebro.plot(iplot=False)  # Set iplot=False to avoid issues with inline plotting
                for fig in figs:
                    st.pyplot(fig[0])  # Display the figure in the Streamlit app
                ''
                st.write(stock_data)  # Display the fetched stock data

else:
    st.warning("Please select valid start and end dates.")

