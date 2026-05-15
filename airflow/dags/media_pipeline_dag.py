import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

PROJECT_ROOT = '/opt/airflow'

with DAG(
    dag_id='media_trends_pipeline',
    default_args=default_args,
    description='Pipeline ETL de bout en bout pour la plateforme Media Trends',
    schedule_interval='@hourly',
    start_date=datetime(2026, 5, 14),
    catchup=False,
    tags=['media', 'trends', 'etl']
) as dag:

    # Tâche 1a : Scraping Batch
    run_scraper = BashOperator(
        task_id='run_scraper',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "scrapers", "batch_scraper.py")}"'
    )

    # Tâche 1b : Streaming Producer Kafka (en parallèle du batch)
    run_streaming_producer = BashOperator(
        task_id='run_streaming_producer',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "scrapers", "streaming_producer.py")}"'
    )

    # Tâche 1c : Consumer Kafka → Bronze
    run_streaming_consumer = BashOperator(
        task_id='run_streaming_consumer',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "scrapers", "kafka_consumer.py")}"'
    )

    # Tâche 2 : Bronze → Silver
    bronze_to_silver = BashOperator(
        task_id='bronze_to_silver',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "transformations", "bronze_to_silver.py")}"'
    )

    # Tâche 3 : Qualité des données
    data_quality_checks = BashOperator(
        task_id='data_quality_checks',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "quality", "data_quality_checks.py")}"'
    )

    # Tâche 4 : Silver → Gold
    silver_to_gold = BashOperator(
        task_id='silver_to_gold',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "transformations", "silver_to_gold.py")}"'
    )

    # Tâche 5 : Chargement dans PostgreSQL
    load_to_warehouse = BashOperator(
        task_id='load_to_warehouse',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "warehouse", "load_to_postgres.py")}"'
    )

    # Ordre d'exécution :
    # Batch et Streaming tournent en parallèle → puis pipeline ETL
    run_streaming_producer >> run_streaming_consumer
    [run_scraper, run_streaming_consumer] >> bronze_to_silver
    bronze_to_silver >> data_quality_checks >> silver_to_gold >> load_to_warehouse