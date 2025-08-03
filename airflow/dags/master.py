from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
}

with DAG('master',
         default_args=default_args,
         schedule_interval=None) as dag:

    start = EmptyOperator(task_id='start')

    trigger_scrape = TriggerDagRunOperator(
        task_id='trigger_scrape',
        trigger_dag_id='scrape',
        wait_for_completion=True,
    )

    trigger_transform = TriggerDagRunOperator(
        task_id='trigger_transform',
        trigger_dag_id='transform',
        wait_for_completion=True,
    )

    trigger_embed = TriggerDagRunOperator(
        task_id='trigger_embed',
        trigger_dag_id='embed',
        wait_for_completion=True,
    )

    end = EmptyOperator(task_id='end')

    start >> trigger_scrape >> trigger_transform >> trigger_embed >>end