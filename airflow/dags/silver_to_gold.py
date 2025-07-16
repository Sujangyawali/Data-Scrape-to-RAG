from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from src.transform import silver_to_gold

with DAG(
    'silver_to_gold_dag',
    start_date=datetime(2025, 7, 16),
    schedule_interval=None,
    catchup=False
) as dag:
    start_task = PythonOperator(
        task_id='start',
        python_callable=lambda: print("Starting silver to gold transformation")
    )
    
    silver_to_gold_task = PythonOperator(
        task_id='silver_to_gold',
        python_callable=silver_to_gold
    )
    
    end_task = PythonOperator(
        task_id='end',
        python_callable=lambda: print("Finished silver to gold transformation")
    )
    
    start_task >> silver_to_gold_task >> end_task