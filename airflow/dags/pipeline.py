from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from src.scraper import scrape_gutenberg
from src.transform import bronze_to_silver, silver_to_gold
from src.embed import generate_embeddings

with DAG(
    'data_pipeline',
    start_date=datetime(2025, 7, 16),
    schedule_interval=None,
    catchup=False
) as dag:
    scrape_task = PythonOperator(
        task_id='scrape',
        python_callable=scrape_gutenberg
    )
    bronze_to_silver_task = PythonOperator(
        task_id='bronze_to_silver',
        python_callable=bronze_to_silver
    )
    silver_to_gold_task = PythonOperator(
        task_id='silver_to_gold',
        python_callable=silver_to_gold
    )
    embed_task = PythonOperator(
        task_id='embed',
        python_callable=generate_embeddings
    )
    scrape_task >> bronze_to_silver_task >> silver_to_gold_task >> embed_task