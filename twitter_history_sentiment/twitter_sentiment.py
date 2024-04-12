## use historical twitter dataset to show the sentiment of the tweets

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as stat
import re


def read_data():
    company_tweet = pd.read_csv('./dataset/Company_Tweet.csv')
    company = pd.read_csv('./dataset/Company.csv')
    tweet = pd.read_csv('./dataset/Tweet.csv')
    company_value = pd.read_csv('./dataset/CompanyValues.csv')
    tweet_df = pd.merge(company_tweet , tweet , on="tweet_id", how= "inner")
    return company_tweet, company, tweet, company_value


def remove_special_character(tweet):
    # remove the old style retweet text "RT"
    tweet = re.sub(r'^RT[\s]+', '', tweet)
    # remove hyperlinks
    tweet = re.sub(r'https?:\/\/.*[\r\n]*', '', tweet)
    # remove hashtags. only removing the hash # sign from the word
    tweet = re.sub(r'#', '', tweet)
    # remove single numeric terms in the tweet. 
    tweet = re.sub(r'[0-9]', '', tweet)
    return tweet
