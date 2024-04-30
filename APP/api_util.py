import json
from pymongo import MongoClient
from config import Config
import pandas as pd
import numpy as np
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import fear_and_greed
from flask import jsonify


vanderSentimentAnalyzer = SentimentIntensityAnalyzer()




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
    client.close()
    return timestamps, prices


def get_reddit_sentiment():
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['reddit']
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)
    end_timestamp = int(end_date.timestamp())
    start_timestamp = int(start_date.timestamp())
    query = {
        "created_utc": {"$gte": start_timestamp, "$lte": end_timestamp}
    }
    data = list(collection.find(query))
    sentiment_scores_with_comments = {} 
    sentiment_counts_with_comments = {'positive': 0, 'negative': 0, 'neutral': 0}
    sentiment_scores = {} 
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    sentiment_counts_by_date = {}
    for item in data:
        date_str = datetime.utcfromtimestamp(item['created_utc']).strftime('%Y-%m-%d')
        score = item.get('vader_score')
        sentiment = item.get('sentiment')
        comments = item.get('comments')
        if date_str not in sentiment_scores:
            sentiment_scores[date_str] = []
            sentiment_scores_with_comments[date_str] = []
            sentiment_counts_by_date[date_str] = {'positive': 0, 'negative': 0, 'neutral': 0}
        sentiment_counts_by_date[date_str][sentiment] += 1
        sentiment_scores[date_str].append(score)
        sentiment_scores_with_comments[date_str].append(score)
        sentiment_counts[sentiment] += 1
        sentiment_counts_with_comments[sentiment] += 1
        for comment in comments:
            comment_score = comment['vader_score']
            comment_date = datetime.utcfromtimestamp(comment['created_utc']).strftime('%Y-%m-%d')
            comment_sentiment = comment['sentiment']
            if comment_date in sentiment_scores:
                sentiment_scores_with_comments[comment_date].append(comment_score)
                sentiment_counts_with_comments[comment_sentiment] += 1
                sentiment_counts_by_date[comment_date][comment_sentiment] += 1
    average_scores = {date: sum(scores) / len(scores) for date, scores in sentiment_scores.items()}
    average_scores_with_comments = {date: sum(scores) / len(scores) for date, scores in sentiment_scores_with_comments.items()}
    client.close()
    result = {
        'scores': average_scores,
        'sentiment_counts': sentiment_counts,
        'scores_with_comments': average_scores_with_comments,
        'sentiment_counts_with_comments': sentiment_counts_with_comments,
        'sentiment_counts_by_date': sentiment_counts_by_date
    }
    return json.dumps(result, indent=4)


def get_sentiment_by_company(company):
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
    company_reddit_collection = f"{company}_reddit"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat'][company_reddit_collection]
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)
    end_timestamp = int(end_date.timestamp())
    start_timestamp = int(start_date.timestamp())
    query = {
        "created_utc": {"$gte": start_timestamp, "$lte": end_timestamp}
    }
    data = list(collection.find(query))
    sentiment_scores = {} 
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    sentiment_counts_by_date = {}
    for item in data:
        date_str = datetime.utcfromtimestamp(item['created_utc']).strftime('%Y-%m-%d')
        score = item.get('vader_score')
        sentiment = item.get('sentiment')
        comments = item.get('comments')
        if date_str not in sentiment_scores:
            sentiment_scores[date_str] = []
            sentiment_counts_by_date[date_str] = {'positive': 0, 'negative': 0, 'neutral': 0}
        sentiment_counts_by_date[date_str][sentiment] += 1
        sentiment_scores[date_str].append(score)
        sentiment_counts[sentiment] += 1
        for comment in comments:
            comment_score = comment['vader_score']
            comment_date = datetime.utcfromtimestamp(comment['created_utc']).strftime('%Y-%m-%d')
            comment_sentiment = comment['sentiment']
            if comment_date in sentiment_scores:
                sentiment_scores[comment_date].append(comment_score)
                sentiment_counts_by_date[comment_date][comment_sentiment] += 1
                sentiment_counts[sentiment] += 1
    average_scores = {date: sum(scores) / len(scores) for date, scores in sentiment_scores.items()}
    client.close()
    result = {
        'scores': average_scores,
        'sentiment_counts': sentiment_counts,
        'sentiment_counts_by_date': sentiment_counts_by_date
    }
    return json.dumps(result, indent=4)



def getVaderScore(text):
    try:
        vs = vanderSentimentAnalyzer.polarity_scores(text)
        score = vs['compound']
        return score
    except Exception as e:
        logging.error("Failed to compute Vader score: %s", e)
    try:
        vs = vanderSentimentAnalyzer.polarity_scores(text)
        score = vs['compound']
        return score
    except Exception as e:
        logging.error("Failed to compute Vader score: %s", e)


def getVaderSentiment(score):
    if (score >= 0.05):
        return "positive"
    elif (score > -0.05 and score < 0.05):
        return "neutral"
    elif (score <= -0.05):
        return "negative"

def create_fear_greed_gauge(value):  
    plot_bgcolor = "#def"
    quadrant_colors = [plot_bgcolor, "#2bad4e", "#85e043", "#eff229", "#f2a529", "#f25829"] 
    quadrant_text = ["", "<b>EXTREME GREED</b>", "<b>GREED</b>", "<b>NEUTRAL</b>", "<b>FEAR</b>", "<b>EXTREME FEAR</b>"]
    current_value = value
    min_value = 0
    max_value = 100
    hand_length = np.sqrt(2) / 4
    hand_angle = np.pi * (1 - (max(min_value, min(max_value, current_value)) - min_value) / (max_value - min_value))
    values = [0.5, 0.125, 0.1, 0.05, 0.1, 0.125]
    fig = go.Figure(
        data=[
                go.Pie(
                    values = values,
                    rotation=90,
                    hole=0.6,
                    marker_colors=quadrant_colors,
                    text=quadrant_text,
                    textinfo="text",
                    hoverinfo="skip",
                    sort= False
                ),
            ],
            layout=go.Layout(
                showlegend=False,
                margin=dict(b=0,t=10,l=10,r=10),
                width=450,
                height=450,
                paper_bgcolor=plot_bgcolor,
                annotations=[
                    go.layout.Annotation(
                        text=f"<b>Fear and Greed Index:</b><br>{current_value}",
                        x=0.5, xanchor="center", xref="paper",
                        y=0.25, yanchor="bottom", yref="paper",
                        showarrow=False,
                    )
                ],
                shapes=[
                    go.layout.Shape(
                        type="circle",
                        x0=0.48, x1=0.52,
                        y0=0.48, y1=0.52,
                        fillcolor="#333",
                        line_color="#333",
                    ),
                    go.layout.Shape(
                        type="line",
                        x0=0.5, x1=0.5 + hand_length * np.cos(hand_angle),
                        y0=0.5, y1=0.5 + hand_length * np.sin(hand_angle),
                        line=dict(color="#333", width=4)
                    )
                ]
            )
        )
    fig_json = json.dumps(fig, cls= plotly.utils.PlotlyJSONEncoder)
    return fig_json


def get_fear_greed_index():
    data = fear_and_greed.get()
    return data.value



def get_comment_company_count():
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
    collection = "comment"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat'][collection]
    today = datetime.now()
    start_of_day = datetime(today.year, today.month, today.day, 0, 0, 0)
    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
    pipeline = [
        {"$match": 
            {"timestamp": {"$gte": start_of_day, "$lte": end_of_day}
        }},
        {"$group": {"_id": "$company", "count": {"$sum": 1}}}
    ]
    results = list(collection.aggregate(pipeline))
    data = {result['_id']: result['count'] for result in results}
    return jsonify(data)


def backtest_price(start_date, end_date, company):
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['stock_historical_price']
    query = {
        'date': {'$gte': start_date, '$lte': end_date},
        'ticker': company
    }
    fields = {
        'date': 1, 
        'open': 1, 
        'close': 1, 
        'high': 1, 
        'low': 1, 
        'volume': 1,
        '_id': 0,
        'ADJ_Close': 1
    }
    documents = collection.find(query, fields)
    data = []
    for document in documents:
        data.append(document)
    return data


    



if __name__ == '__main__':
    # print(get_realtime_data())
    # print(get_reddit_sentiment())
    print(get_comment_company_count())
