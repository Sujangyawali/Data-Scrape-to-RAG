install:
	pip install -r requirements.txt

run_all:
	docker-compose up -d
	python -m airflow dags trigger data_pipeline

test:
	pytest tests/

clean:
	docker-compose down
	rm -rf airflow/airflow.db