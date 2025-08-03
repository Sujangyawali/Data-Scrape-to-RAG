from datetime import datetime
from airflow import DAG
from docker_exec_operator import DockerExecOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
}

with DAG('embed',
         default_args=default_args,
         schedule_interval=None) as dag:
    start_task = EmptyOperator(task_id='start')

    run_embed = DockerExecOperator(
        task_id='run_embedding',
        container_name='rag_app',
        command=["python3", "/app/embeddings.py"]
    )

    end_task = EmptyOperator(task_id='end')
    start_task >> run_embed >> end_task