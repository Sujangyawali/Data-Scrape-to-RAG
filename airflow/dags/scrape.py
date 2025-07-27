from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import sys
from openlineage.client.run import Dataset, RunEvent, RunState
from openlineage.client.client import OpenLineageClient
from openlineage.client.facet import DocumentationJobFacet

sys.path.append('/opt/airflow/src')
print(f"sys.path:", sys.path)
from scraper import scrape_gutenberg

# Initialize OpenLineage client with correct Marquez base URL
client = OpenLineageClient(url="http://marquez:8080")

with DAG(
    dag_id='scrape',
    start_date=datetime(2025, 7, 16),
    schedule_interval=None,
    catchup=False
) as dag:
    start_task = EmptyOperator(
        task_id='start'
    )

    def scrape_gutenberg_with_lineage(**context):
        # Call the original function without passing context
        result = scrape_gutenberg()

        # Define datasets
        input_dataset = Dataset(
            namespace="https://www.gutenberg.org",
            name="/opt/airflow/data/input_data",
            facets={
        "documentation": DocumentationJobFacet(
            description="Source having all incoming scraped books and metadata as json files"
        )
    }
        )
        output_dataset = Dataset(
            namespace="http://localhost:9001",
            name="http://localhost:9001/browser/raw/books/",
            facets={
        "documentation": DocumentationJobFacet(
            description="Raw layer containing all incoming scraped books and metadata as json files"
        )
    }
        )

        # Emit OpenLineage START event
        client.emit(
            RunEvent(
                eventType=RunState.START,
                eventTime=datetime.utcnow().isoformat(),
                run={"runId": context["run_id"]},
                job={"namespace": "scrap-to-rag", "name": "scrape.scrape"},
                producer="https://github.com/OpenLineage/OpenLineage",
                inputs=[input_dataset],
                outputs=[output_dataset]
            )
        )

        # Emit OpenLineage COMPLETE event
        client.emit(
            RunEvent(
                eventType=RunState.COMPLETE,
                eventTime=datetime.utcnow().isoformat(),
                run={"runId": context["run_id"]},
                job={"namespace": "scrap-to-rag", "name": "scrape.scrape"},
                producer="https://github.com/OpenLineage/OpenLineage",
                inputs=[input_dataset],
                outputs=[output_dataset]
            )
        )

        return result

    scrape_task = PythonOperator(
        task_id='scrape',
        python_callable=scrape_gutenberg_with_lineage,
        provide_context=True
    )

    end_task = EmptyOperator(
        task_id='end'
    )

    start_task >> scrape_task >> end_task