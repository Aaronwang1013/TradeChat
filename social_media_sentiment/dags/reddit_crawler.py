import praw
from datetime import datetime, timedelta
from praw.models import MoreComments
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
from pymongo.mongo_client import MongoClient
import re
import emoji
from config import Config
import logging


# set up logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

vanderSentimentAnalyzer = SentimentIntensityAnalyzer()

# reddit api
reddit = praw.Reddit(client_id=Config.REDDIT_CLIENT_ID,
                     client_secret=Config.REDDIT_CLIENT_SECRET,
                     username=Config.REDDIT_USER_NAME,
                     password=Config.REDDIT_PASSWORD,
                     user_agent=Config.REDDIT_USER_AGENT)


def get_subreddit_posts(subreddit_name):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        hot_posts = subreddit.hot()
        return hot_posts
    except Exception as e:
        logging.error("Failed to get subreddit posts: %s", e)

def parse_comment(posts):
    # run the script at a new day to get the data of the previous day
    current_date = datetime.utcnow() - timedelta(days=1)
    end_time = current_date.replace(hour=23, minute=59, second=59, microsecond=59)
    start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
    data = []
    try:
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
    except Exception as e:
        logging.error("Failed to parse comment: %s", e)
    




def getVaderScore(text):
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


def clean_comment(comment):
    try:
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
    except Exception as e:
        logging.error("Failed to clean comment: %s", e)


def insert_to_mongo(data):
    try:
        inserted_at = datetime.utcnow().isoformat(timespec="seconds")
        DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(DATABASE_URL)
        collection = client['TradeChat']['reddit']
        data = json.loads(data)
        if data:
            collection.insert_many(data)
        client.close()
        logging.info(f"{len(data)} data inserted to MongoDB at: {inserted_at}.")
    except Exception as e:
        logging.error("Failed to insert data to MongoDB: %s", e)

