import praw
from datetime import datetime, timedelta
from praw.models import MoreComments
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
from pymongo.mongo_client import MongoClient
import re
import emoji
from config import Config

vanderSentimentAnalyzer = SentimentIntensityAnalyzer()

# reddit api
reddit = praw.Reddit(client_id=Config.REDDIT_CLIENT_ID,
                     client_secret=Config.REDDIT_CLIENT_SECRET,
                     username=Config.REDDIT_USER_NAME,
                     password=Config.REDDIT_PASSWORD,
                     user_agent=Config.REDDIT_USER_AGENT)


def get_subreddit_posts(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    hot_posts = subreddit.hot(limit=50)
    return hot_posts

def parse_comment(posts):
    # transfer to US time
    end_time = datetime.utcnow( )- timedelta(hours=4)
    start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
    data = []
    for post in posts:
        if post.created_utc >= start_time.timestamp() and post.created_utc <= end_time.timestamp():
            post_data = {
                "title": clean_comment(post.title),
                "body": clean_comment(post.selftext),
                "created_utc": post.created_utc,
                "author": post.author.name if post.author else "Unknown",
                "vader_score": getVaderScore(post.title + " " + post.selftext),
                "sentiment": getVaderSentiment(getVaderScore(post.title + " " + post.selftext)),
                "comments": []
            }
            if len(post.comments) > 0:
                for comment in post.comments:
                     # ignore morecomments, cause most of them are not related to the sentiment
                    if isinstance(comment, MoreComments):
                        continue
                    comment_author = comment.author.name if comment.author else "Unknown"
                    comment_data = {
                        "body": clean_comment(comment.body),
                        "created_utc": comment.created_utc,
                        "author": comment_author,
                        "vader_score": getVaderScore(comment.body),
                        "sentiment": getVaderSentiment(getVaderScore(comment.body))
                    }
                    post_data["comments"].append(comment_data)
            data.append(post_data)
    json_data = json.dumps(data)
    return json_data




def getVaderScore(text):
    vs = vanderSentimentAnalyzer.polarity_scores(text)
    score = vs['compound']
    return score


def getVaderSentiment(score):
    if (score >= 0.05):
        return "positive"
    elif (score > -0.05 and score < 0.05):
        return "neutral"
    elif (score <= -0.05):
        return "negative"


def clean_comment(comment):
    # remove emoji
    comment = emoji.demojize(comment)
    # remove words with '/u/' and '@'
    comment = re.sub(r"@\S+|/u/\S+", "", comment)
    # remove special characters and numbers
    comment = re.sub(r"[^a-zA-Z\s]", "", comment)
    # convert to lowercase
    comment = comment.lower()
    # remove extra spaces
    comment = " ".join(comment.split())
    return comment


def insert_to_mongo(data):
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['reddit']
    data = json.loads(data)
    if data:
        collection.insert_many(data)
    client.close()



# if __name__ == '__main__':
#     ticker = ['AAPL', 'TSLA', 'AAPL', 'NVDA_Stock', 'MSFT', 'amzn',
#             'meta', 'google', 'stock', 'investing', 'StockMarket', 
#             'wallstreetbets']
#     # ticker = ['AAPL']
#     # ticker = ['wallstreetbets']
#     for i in ticker:
#         posts = get_subreddit_posts(i)
#         data = parse_comment(posts)

#         insert_to_mongo(data)