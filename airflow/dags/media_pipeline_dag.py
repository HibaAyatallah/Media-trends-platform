import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Définition des arguments par défaut pour les tâches du DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Déduction automatique du chemin racine du projet pour assurer la portabilité du code
DAGS_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(DAGS_FOLDER))

# Initialisation du DAG
with DAG(
    dag_id='media_trends_pipeline',
    default_args=default_args,
    description='Pipeline ETL de bout en bout pour la plateforme Media Trends',
    schedule_interval='@hourly',      # Exécution toutes les heures
    start_date=datetime(2026, 5, 14), # Date de démarrage récente
    catchup=False,                    # Désactive le rattrapage des exécutions manquées
    tags=['media', 'trends', 'etl']
) as dag:

    # ---------------------------------------------------------
    # Tâche 1 : Ingestion des données brutes
    # ---------------------------------------------------------
    # Exécute le scraper batch pour collecter les nouveaux articles
    # et les stocke dans la couche Bronze.
    run_scraper = BashOperator(
        task_id='run_scraper',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "scrapers", "batch_scraper.py")}"'
    )

    # ---------------------------------------------------------
    # Tâche 2 : Transformation Bronze vers Silver
    # ---------------------------------------------------------
    # Nettoie, standardise les données brutes et filtre les anomalies.
    # Sauvegarde le résultat dans la couche Silver.
    bronze_to_silver = BashOperator(
        task_id='bronze_to_silver',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "transformations", "bronze_to_silver.py")}"'
    )

    # ---------------------------------------------------------
    # Tâche 3 : Contrôles de qualité
    # ---------------------------------------------------------
    # Lit les données Silver et génère un rapport de qualité
    # (champs manquants, doublons, etc.).
    data_quality_checks = BashOperator(
        task_id='data_quality_checks',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "quality", "data_quality_checks.py")}"'
    )

    # ---------------------------------------------------------
    # Tâche 4 : Transformation Silver vers Gold
    # ---------------------------------------------------------
    # Crée les tables d'agrégation analytiques (CSVs) pour le reporting.
    silver_to_gold = BashOperator(
        task_id='silver_to_gold',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "transformations", "silver_to_gold.py")}"'
    )

    # ---------------------------------------------------------
    # Tâche 5 : Chargement dans le Data Warehouse
    # ---------------------------------------------------------
    # Insère les données analytiques Gold dans la base de données PostgreSQL.
    load_to_warehouse = BashOperator(
        task_id='load_to_warehouse',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "warehouse", "load_to_postgres.py")}"'
    )

    # ---------------------------------------------------------
    # Définition des dépendances (Ordre d'exécution)
    # ---------------------------------------------------------
    run_scraper >> bronze_to_silver >> data_quality_checks >> silver_to_gold >> load_to_warehouse
