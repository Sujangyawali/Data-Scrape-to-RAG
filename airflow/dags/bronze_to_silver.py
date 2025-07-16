from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from src.transform import bronze_to_silver

with DAG(
    'bronze_to_silver_dag',
    start_date=datetime(2025, 7, 16),
    schedule_interval=None,
    catchup=False
) as dag:
    start_task = PythonOperator(
        task_id='start',
        python_callable=lambda: print("Starting bronze to silver transformation")
    )
    
    bronze_to_silver_task = PythonOperator(
        task_id='bronze_to_silver',
        python_callable=bronze_to_silver
    )
    
    end_task = PythonOperator(
        task_id='end',
        python_callable=lambda: print("Finished bronze to silver transformation")
    )

    start_task >> bronze_to_silver_task >> end_task