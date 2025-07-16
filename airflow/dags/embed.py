from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from src.embed import generate_embeddings

with DAG(
    'embed_dag',
    start_date=datetime(2025, 7, 16),
    schedule_interval=None,
    catchup=False
) as dag:
    start_task = PythonOperator(
        task_id='start',
        python_callable=lambda: print("Starting the embedding task")
    )
    
    embed_task = PythonOperator(
        task_id='embed',
        python_callable=generate_embeddings
    )
    
    end_task = PythonOperator(
        task_id='end',
        python_callable=lambda: print("Embedding task completed")
    )
    
    start_task >> embed_task >> end_task