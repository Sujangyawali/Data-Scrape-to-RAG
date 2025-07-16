from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime
# from src.scrapper import scrape_gutenberg

with DAG(
    'scrape_dag',
    start_date=datetime(2025, 7, 16),
    schedule_interval=None,
    catchup=False
) as dag:
    start_task = EmptyOperator(
    task_id='start'
)
    
    # scrape_task = PythonOperator(
    #     task_id='scrape',
    #     python_callable=scrape_gutenberg
    # )
    
    end_task = EmptyOperator(
    task_id='end'
)
    
    start_task >> end_task