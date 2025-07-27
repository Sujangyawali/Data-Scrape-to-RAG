from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
from openlineage.client.client import OpenLineageClient
from openlineage.client.run import Dataset, RunEvent, RunState
import uuid
import os
from openlineage.client.facet import DocumentationJobFacet

# Unique container name
unique_name = f"pyspark_service_{str(uuid.uuid4())[:8]}"

# Initialize OpenLineage client (adjust Marquez host if needed)
client = OpenLineageClient(url="http://marquez:8080")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}

with DAG(
    dag_id='spark_transform_dag',
    default_args=default_args,
    description='Trigger transform.py bronze_to_silver on pyspark service',
    schedule_interval=None,
    start_date=datetime(2025, 7, 23),
    catchup=False,
) as dag:

    start_task = EmptyOperator(task_id='start')

    def run_with_lineage(**context):
        from airflow.providers.docker.operators.docker import DockerOperator

        run_id = context["run_id"]

        # Define datasets
        input_dataset = Dataset(
            namespace="http://localhost:9001",
            name="http://localhost:9001/browser/raw/books/",
            facets={
        "documentation": DocumentationJobFacet(
            description="Raw layer containing all incoming scraped books and metadata as json files"
        )
    }
        )
        output_dataset = Dataset(
            namespace="http://localhost:9001",
            name="http://localhost:9001/browser/gold/books/",
            facets={
        "documentation": DocumentationJobFacet(
            description="Gold layer output from daily Spark transformations to produced clean data for RAG"
        )
    }
        )

        # Emit START
        client.emit(
            RunEvent(
                eventType=RunState.START,
                eventTime=datetime.utcnow().isoformat(),
                run={"runId": run_id},
                job={"namespace": "default", "name": "spark_transform_dag.raw_to_gold"},
                producer="https://github.com/OpenLineage/OpenLineage",
                inputs=[input_dataset],
                outputs=[output_dataset]
            )
        )

        # Run Spark transformation via DockerOperator
        docker_operator = DockerOperator(
            task_id='raw_to_gold_internal',
            image='bitnami/spark:latest',
            container_name=unique_name,
            command='bash -c "pip install -r /opt/spark/requirements-pyspark.txt && python3 /opt/spark/src/transform.py bronze_to_silver"',
            docker_url='unix://var/run/docker.sock',
            mount_tmp_dir=False,
            auto_remove=True,
            network_mode='host',
            mounts=[
                Mount(source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/src', target='/opt/spark/src', type='bind'),
                Mount(source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/sample_config', target='/opt/spark/sample_config', type='bind'),
                Mount(source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/data', target='/opt/spark/data', type='bind'),
                Mount(source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/.env', target='/opt/spark/.env', type='bind'),
                Mount(source='/host_mnt/d/Projects/Assignment/Data-Scrape-to-RAG/requirements-pyspark.txt', target='/opt/spark/requirements-pyspark.txt', type='bind')
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
            dag=dag,
        )
        docker_operator.execute(context=context)

        # Emit COMPLETE
        client.emit(
            RunEvent(
                eventType=RunState.COMPLETE,
                eventTime=datetime.utcnow().isoformat(),
                run={"runId": run_id},
                job={"namespace": "default", "name": "spark_transform_dag.raw_to_gold"},
                producer="https://github.com/OpenLineage/OpenLineage",
                inputs=[input_dataset],
                outputs=[output_dataset]
            )
        )

    run_transform_with_lineage = PythonOperator(
        task_id='raw_to_gold',
        python_callable=run_with_lineage,
        provide_context=True
    )

    end_task = EmptyOperator(task_id='end')

    start_task >> run_transform_with_lineage >> end_task