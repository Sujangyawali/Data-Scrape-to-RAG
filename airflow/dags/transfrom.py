from datetime import datetime
from airflow import DAG
from docker_exec_operator import DockerExecOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
}

with DAG('transform',
         default_args=default_args,
         schedule_interval=None) as dag:
    start_task = EmptyOperator(task_id='start')

    run_spark = DockerExecOperator(
        task_id='spark_transform',
        container_name='data-scrape-to-rag-pyspark-1',
        command=["bash", "-c", "python3 /opt/spark/src/transform.py bronze_to_silver"]
    )

    end_task = EmptyOperator(
        task_id='end'
    )
    start_task >> run_spark >> end_task