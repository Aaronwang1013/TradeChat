import json
from pymongo import MongoClient
from config import Config
import pandas as pd
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd


def read_twitter_data(company=None):
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    tweet_collection = client['TradeChat']['Twitter_tweets']
    stock_collection = client['TradeChat']['Twitter_stock']
    target_company = {}
    if company:
        target_company['ticker_symbol'] = company
    # Retrieve all the collections
    tweet_data = list(tweet_collection.find(target_company))
    stock_data = list(stock_collection.find(target_company))
    tweet_df = pd.DataFrame(tweet_data)
    tweet_df['day_date'] = pd.to_datetime(tweet_df['day_date'], unit='ms')
    stock_df = pd.DataFrame(stock_data)
    stock_df['day_date'] = pd.to_datetime(stock_df['day_date'], unit='ms')
    client.close()
    return tweet_df, stock_df


def sentiment_overtime(tweet_df, stock_df, title, score_column_name="score", save_path=None):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=tweet_df['day_date'], y=tweet_df[score_column_name], mode='lines', name=score_column_name),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=stock_df['day_date'], y=stock_df['close_value'], mode='lines', name='Stock Price'),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"Effects of {title} tweets to stock price",
        xaxis_title="Day date",
        yaxis_title=score_column_name,
        yaxis2_title="Stock Price",
    )
    fig.update_xaxes(type='date')
    fig_json = json.dumps(fig, cls= plotly.utils.PlotlyJSONEncoder)
    return fig_json



def draw_stock_price_with_sentiment(tweet_df, stock_df, start_day, end_day, company_name, score_name="score"):
    company = company_name
    sub_tweet_df = tweet_df[tweet_df["ticker_symbol"] == company]
    sub_tweet_df = sub_tweet_df[(sub_tweet_df["day_date"]>=start_day) & (sub_tweet_df["day_date"]<=end_day)]
    sub_stock_df = stock_df[stock_df["ticker_symbol"] == company]
    sub_stock_df = sub_stock_df[(sub_stock_df["day_date"]>=start_day) & (sub_stock_df["day_date"]<=end_day)]
    fig_json = sentiment_overtime(sub_tweet_df, sub_stock_df, company_name)
    return fig_json


def get_realtime_data():
    #connect to mongodb
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['stock_realtime_price']
    latest_data = collection.find().sort([('_id', -1)]).limit(100)
    timestamps = []
    prices = []
    for record in latest_data:
        timestamps.append(record['timestamp'])
        prices.append(record['price'])
    return timestamps, prices


if __name__ == '__main__':
    print(get_realtime_data())