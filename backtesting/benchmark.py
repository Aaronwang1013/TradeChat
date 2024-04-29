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

df['ma20'] = df['Adj Close'].rolling(window=20).mean()
df['std'] = df['Adj Close'].rolling(window=20).std()
df['upper_band'] = df['ma20'] + (2 * df['std'])
df['lower_band'] = df['ma20'] - (2 * df['std'])
df.drop(['Open','High','Low'],axis=1,inplace=True,errors='ignore')
print(df.tail(5))