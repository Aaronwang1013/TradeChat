# Importing necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import pyfolio as pf
import datetime as dt
import pandas_datareader.data as web
import os
import warnings
from config import Config
from pymongo import MongoClient
from datetime import datetime

# print all outputs
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"


_start = dt.date(2015,1,2)
_end = dt.date(2020,4,30)
ticker = 'MSFT'
df = yf.download(ticker, start = _start, end = _end)
df['bnh_returns'] = np.log(df['Adj Close']/df['Adj Close'].shift(1))
investment = 1000
initial_price = df['Close'].iloc[0]
shares_bought = investment / initial_price

# Calculate the value of the investment over time
df['Portfolio Value'] = shares_bought * df['Close']
print(df)
# Create a plot to show the value of the investment over time
plt.figure(figsize=(12, 6))
plt.plot(df['Portfolio Value'], label=f'Buy and Hold')
plt.title(f'Investment Value of ${investment} in {ticker} Over Time')
plt.xlabel('Date')
plt.ylabel('Portfolio Value (USD)')
plt.legend()
plt.grid(True)
plt.show()
