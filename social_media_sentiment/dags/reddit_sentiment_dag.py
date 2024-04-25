from airflow import DAG
from datetime import timedelta
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

import pendulum
## reddit crawler
import reddit_crawler



tickers = ['AAPL', 'TSLA', 'NVDA_Stock', 'MSFT', 'amzn',
        'meta', 'google']

categories = ['stock', 'investing', 'StockMarket', 
        'wallstreetbets']

def get_reddit_post():
    for i in categories:
        posts = reddit_crawler.get_subreddit_posts(i)
        data = reddit_crawler.parse_comment(posts)
        reddit_crawler.insert_to_mongo(data)

def get_reddit_by_company():
    for i in tickers:
        posts = reddit_crawler.get_subreddit_posts(i)
        data = reddit_crawler.parse_comment(posts)
        reddit_crawler.insert_to_mongo_by_company(data)



default_args = {
    'owner': 'airflow',
    'depends_on_past': False, 
    "start_date": days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

local_tz = pendulum.timezone("Asia/Taipei")

with DAG(
    "reddit_sentiment_dag",
    default_args=default_args,
    schedule="0 0 * * *",
    catchup=False
) as dag:
    task_start = EmptyOperator(
        task_id="task_start",
        dag=dag
    )

    task_end = EmptyOperator(
        task_id="task_end",
        dag=dag
    )

    reddit_sentiment = PythonOperator(
        task_id="reddit_sentiment",
        python_callable=get_reddit_post,
        dag=dag
    )
    reddit_sentiment_by_company = PythonOperator(
        task_id="reddit_sentiment_by_company",
        python_callable=get_reddit_by_company,
        dag=dag
    )


    (task_start >> reddit_sentiment >> reddit_sentiment_by_company >> task_end)