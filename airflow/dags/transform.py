from datetime import datetime
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.empty import EmptyOperator
from docker.types import Mount
import uuid


unique_name = f"pyspark_service_{str(uuid.uuid4())[:8]}"
# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}

# Define the DAG
with DAG(
    dag_id='spark_transform_dag',
    default_args=default_args,
    description='Trigger transform.py bronze_to_silver on pyspark service',
    schedule_interval=None,  # Set to None or a cron expression as needed
    start_date=datetime(2025, 7, 23),
    catchup=False,
) as dag:
    
    start_task = EmptyOperator(
    task_id='start'
    )

    # Task to run transform.py in the pyspark container
    run_transform = DockerOperator(
        task_id='run_bronze_to_silver',
        image='bitnami/spark:latest',
        container_name=unique_name,
        command='bash -c "pip install -r /opt/spark/requirements-pyspark.txt && python3 /opt/spark/src/transform.py bronze_to_silver"',
        docker_url='unix://var/run/docker.sock',
        mount_tmp_dir=False,
        auto_remove=True, 
        network_mode='host',
        mounts=[
            Mount(
                source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/src',
                target='/opt/spark/src',
                type='bind'
            ),
            Mount(
            source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/sample_config',
            target='/opt/spark/sample_config',
            type='bind'
            ),
            Mount(
                source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/data',
                target='/opt/spark/data',
                type='bind'
            ),
            Mount(
                source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/.env',
                target='/opt/spark/.env',
                type='bind'
            ),
            Mount(
                source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/requirements-pyspark.txt',
                target='/opt/spark/requirements-pyspark.txt',
                type='bind'
            )
        ],
        environment={
            'SPARK_MODE': 'master',
            'SPARK_RPC_AUTHENTICATION_ENABLED': 'no',
            'SPARK_RPC_ENCRYPTION_ENABLED': 'no',
            'SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED': 'no',
            'SPARK_SSL_ENABLED': 'no',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'minioadmin',
            'MINIO_SECRET_KEY': 'minioadmin',
        },
    )
    end_task = EmptyOperator(
        task_id='end'
    )

    start_task >> run_transform >> end_task