from airflow import DAG
from datetime import timedelta, datetime
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
import logging
import pendulum
## reddit crawler
import reddit_crawler


# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ticker = ['AAPL', 'TSLA', 'AAPL', 'NVDA_Stock', 'MSFT', 'amzn',
        'meta', 'google', 'stock', 'investing', 'StockMarket', 
        'wallstreetbets']

def get_reddit_post():
    for i in ticker:
        posts = reddit_crawler.get_subreddit_posts(i)
        data = reddit_crawler.parse_comment(posts)
        reddit_crawler.insert_to_mongo(data)



default_args = {
    'owner': 'airflow',
    'depends_on_past': False, 
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


dag = DAG(
    "reddit_sentiment_dag",
    default_args=default_args,
    # utc 59:03 to US 59:23
    schedule="59 03 * * *",
    catchup=False,
    start_date=datetime.today()
)


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


(task_start >> reddit_sentiment >> task_end)