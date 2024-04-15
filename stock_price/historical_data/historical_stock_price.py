import yfinance as yf
import pandas as pd
from pymongo.mongo_client import MongoClient
from config import Config




def extract_ticker(tickers, start_date, end_date):
    for ticker in tickers:
        data = yf.download(ticker, start=start_date, end=end_date)
        df = pd.DataFrame(data)
        for i in range(len(df)):
            stock_data = {
                "ticker": ticker,
                "date": df.iloc[i].name,
                "open": df.iloc[i]['Open'],
                "high": df.iloc[i]['High'],
                "low": df.iloc[i]['Low'],
                "close": df.iloc[i]['Close'],
                "volume": df.iloc[i]['Volume']
            }
            insert_to_mongo(stock_data)
    


def insert_to_mongo(data):
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['stock_historical_price']
    if data:
        collection.insert_one(data)
    client.close()



if __name__ == '__main__':
    tickers = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOG']
    extract_ticker(tickers, '2000-01-01', '2024-04-12')