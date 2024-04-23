from airflow import DAG
from datetime import timedelta, datetime
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
import historical_stock_price
from airflow.utils.dates import days_ago



def get_stock_price():
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_date = monday.strftime('%Y-%m-%d')
    end_date = (monday + timedelta(days=6)).strftime('%Y-%m-%d')
    tickers = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOG']
    historical_stock_price.extract_ticker(tickers, start_date, end_date)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False, 
    "start_date": days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}



with DAG(
    "reddit_sentiment_dag",
    default_args=default_args,
    schedule="0 0 * * 0",
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

    historical_stock_price_dag = PythonOperator(
        task_id="historical_stock_price",
        python_callable=get_stock_price,
        dag=dag
    )


    (task_start >> historical_stock_price_dag >> task_end)