from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import sys
sys.path.append('/opt/airflow/src')
print(f"sys.path:", sys.path)
from scraper import scrape_gutenberg

with DAG(
    'scrape',
    start_date=datetime(2025, 7, 16),
    schedule_interval=None,
    catchup=False
) as dag:
    start_task = EmptyOperator(
    task_id='start'
)

    scrape_task = PythonOperator(
        task_id='scrape',
        python_callable=scrape_gutenberg
    )

    end_task = EmptyOperator(
    task_id='end'
)

    start_task >> scrape_task >> end_task