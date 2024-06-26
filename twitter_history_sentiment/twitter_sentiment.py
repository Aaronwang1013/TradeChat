## use historical twitter dataset to show the sentiment of the tweets

import pandas as pd
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pymongo.mongo_client import MongoClient
from config import Config
import json

vanderSentimentAnalyzer = SentimentIntensityAnalyzer()


def read_data():
    company_tweet = pd.read_csv('./dataset/Company_Tweet.csv')
    tweet = pd.read_csv('./dataset/Tweet.csv')
    company_value = pd.read_csv('./dataset/CompanyValues.csv')
    return company_tweet,tweet, company_value


def get_tweet_df(company_tweet, tweet):
    """
    merge company_tweet and tweet dataframes, and preprocess the data
    """
    tweet_df = pd.merge(company_tweet , tweet , on="tweet_id", how= "inner")
    tweet_df['post_date'] = pd.to_datetime(tweet_df['post_date'], unit='s')
    tweet_df['day_date'] = pd.to_datetime(tweet_df['post_date'].apply(lambda date: date.date()))
    tweet_df = tweet_df.sort_values(by="day_date")
    tweet_df['total_engangement'] = tweet_df['comment_num'] + tweet_df['retweet_num'] + tweet_df['like_num']
    engagement_threshold = 40
    tweet_df = tweet_df[tweet_df["total_engangement"] > engagement_threshold]
    tweet_df = tweet_df.drop(['tweet_id', 'post_date', 'comment_num', 'retweet_num', 'like_num'], axis=1)
    return tweet_df

def remove_special_characters(tweet):
    """
    remove hyperlinks, hashtags, old style retweet text, and single numeric terms
    """
    tweet = re.sub(r'^RT[\s]+', '', tweet)
    tweet = re.sub(r'https?:\/\/.*[\r\n]*', '', tweet)
    tweet = re.sub(r'#', '', tweet)
    tweet = re.sub(r'[0-9]', '', tweet)
    return tweet


def text_preprocessing(tweet_df):
    """
    tweet preprocessing, remove special characters, and convert to lowercase
    """
    tweet_df['tweet'] = tweet_df['body'].apply(lambda tweet: remove_special_characters(tweet))
    tweet_df['tweet'] = tweet_df['tweet'].str.lower()
    return tweet_df


def getVanderScore(tweet):    
    vs = vanderSentimentAnalyzer.polarity_scores(tweet)
    score = vs['compound']
    return score

def getVanderSentiment(score):    
    if (score >= 0.05): 
        return "Positive"
    
    elif (score < 0.05 and score > -0.05):
        return "Neutral"
    
    elif (score <= -0.05):    
        return "Negative"
    
    return score



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

    return fig



def draw_stock_price_with_sentiment(tweet_df, stock_df, start_day, end_day, score_name="score"):
    ticker_symbols =  tweet_df["ticker_symbol"].unique()
    company = pd.read_csv('./dataset/Company.csv')
    for ticker_symbol in ticker_symbols:
        print(f"Ticker symbol: {ticker_symbol}")

        sub_company = company[company["ticker_symbol"] == ticker_symbol]["company_name"]
        if len(sub_company) != 1:
            continue

        company_name = sub_company.iloc[0]

        print(f"Stock price of {company_name} company with ticker symbol is {ticker_symbol}")

        sub_tweet_df = tweet_df[tweet_df["ticker_symbol"] == ticker_symbol]
        sub_tweet_df = sub_tweet_df[(sub_tweet_df["day_date"]>=pd.to_datetime(start_day)) & (sub_tweet_df["day_date"]<=pd.to_datetime(end_day))]

        sub_stock_df = stock_df[stock_df["ticker_symbol"] == ticker_symbol]
        sub_stock_df = sub_stock_df[(sub_stock_df["day_date"]>=pd.to_datetime(start_day)) & (sub_stock_df["day_date"]<=pd.to_datetime(end_day))]
        save_path = f"./images/{ticker_symbol}_sentiment_overtime.png"
        sentiment_overtime(sub_tweet_df, sub_stock_df, company_name, score_column_name=score_name, save_path = save_path)

def store_in_db(tweet_df, stock_df):
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    tweet_data = json.loads(tweet_df)
    stock_data = json.loads(stock_df)
    collection = client['TradeChat']['Twitter_tweets']
    collection.insert_many(tweet_data)
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['Twitter_stock']
    collection.insert_many(stock_data)

if __name__ == '__main__':
    stock_df, tweet_df, company_value = read_data()
    tweet_df = get_tweet_df(stock_df, tweet_df)
    tweet_df = text_preprocessing(tweet_df)
    tweet_df['score'] = tweet_df['tweet'].apply(lambda tweet: getVanderScore(tweet))
    tweet_df['sentiment'] = tweet_df['score'].apply(lambda score: getVanderSentiment(score))
    stock_df = company_value
    stock_df['day_date']  = pd.to_datetime(stock_df['day_date'])
    start_day = min(tweet_df['day_date'])
    end_day = max(tweet_df['day_date'])
    stock_df = stock_df[(stock_df['day_date'] >= start_day) & (stock_df['day_date'] <= end_day)]
    stock_df = stock_df.sort_values(by="day_date")
    stock_json = stock_df.to_json(orient="records")
    tweet_json = tweet_df.to_json(orient="records")
    store_in_db(tweet_json, stock_json)
