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



# DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# client = MongoClient(DATABASE_URL)
# # initialize collection
# collection = client['TradeChat']['stock_historical_price']



# start_date = datetime(2015,1,1)
# end_date = datetime(2020,12,31)


# query = {
#     'date': {'$gte': start_date, '$lte': end_date}
# }


# documents = collection.find(query)
# count = 0
# for document in documents:
#     count +=1
#     print(document)


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

# df['ma20'] = df['Adj Close'].rolling(window=20).mean()
# df['std'] = df['Adj Close'].rolling(window=20).std()
# df['upper_band'] = df['ma20'] + (2 * df['std'])
# df['lower_band'] = df['ma20'] - (2 * df['std'])
# df.drop(['Open','High','Low'],axis=1,inplace=True,errors='ignore')


# ## Buy condition
# df['signal'] = np.where((df['Adj Close'] < df['lower_band']) &
#                         (df['Adj Close'].shift(1) >=       df['lower_band']),1,0)

# # SELL condition
# df['signal'] = np.where( (df['Adj Close'] > df['upper_band']) &
#                           (df['Adj Close'].shift(1) <= df['upper_band']),-1,df['signal'])
# # creating long and short positions 
# df['position'] = df['signal'].replace(to_replace=0, method='ffill')

# # shifting by 1, to account of close price return calculations
# df['position'] = df['position'].shift(1)

# # calculating stretegy returns
# df['strategy_returns'] = df['bnh_returns'] * (df['position'])


# print("Buy and hold returns:",df['bnh_returns'].cumsum()[-1])
# print("Strategy returns:",df['strategy_returns'].cumsum()[-1])

# # plotting strategy historical performance over time
# df[['bnh_returns','strategy_returns']] = df[['bnh_returns','strategy_returns']].cumsum()
# df[['bnh_returns','strategy_returns']].plot(grid=True, figsize=(12, 8))


# pf.create_simple_tear_sheet(df['strategy_returns'].diff())