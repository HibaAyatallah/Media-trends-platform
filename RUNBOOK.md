# Runbook - Media Trends Platform

Ce document est un guide étape par étape (Playbook/Runbook) pour lancer, tester et utiliser l'intégralité de la plateforme.

## Étape 1 : Installation et Préparation
1. Ouvrez un terminal (PowerShell ou Bash) dans le dossier du projet : `c:\Users\hibaa\OneDrive\Desktop\media-trends-platform`
2. Créez un environnement virtuel Python (fortement recommandé) :
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # (Sur Windows)
   ```
3. Installez les dépendances locales :
   ```bash
   pip install -r requirements.txt
   ```

## Étape 2 : Configuration
L'infrastructure est pré-configurée pour fonctionner en local sans configuration supplémentaire complexe grâce au fichier `docker-compose.yml`. Vérifiez simplement qu'aucun de vos ports vitaux (5432, 8080, 8501, 9000, 9092) n'est occupé par une autre application.

## Étape 3 : Lancement avec Docker
Démarrez l'infrastructure Big Data (PostgreSQL, Kafka, MinIO, Airflow, Streamlit) :
```bash
docker-compose up -d
```
*Patientez environ 1 à 2 minutes lors du premier lancement pour qu'Airflow initialise sa base de données.*

## Étape 4 : Test Manuel du Pipeline de Données
Pour vérifier que l'ingénierie de la donnée fonctionne, exécutez ces commandes l'une après l'autre :

1. **Extraction (Bronze)** :
   ```bash
   python scrapers/batch_scraper.py
   ```
2. **Nettoyage (Silver)** :
   ```bash
   python transformations/bronze_to_silver.py
   ```
3. **Contrôle Qualité** :
   ```bash
   python quality/data_quality_checks.py
   ```
4. **Agrégation (Gold)** :
   ```bash
   python transformations/silver_to_gold.py
   ```
5. **Chargement BDD** :
   ```bash
   python warehouse/load_to_postgres.py
   ```

## Étape 5 : Test du Pipeline Automatisé (Airflow)
Au lieu de lancer les scripts manuellement :
1. Accédez à l'interface Airflow : `http://localhost:8080`
2. Connectez-vous avec `admin` / `admin`.
3. Trouvez le DAG `media_trends_pipeline`.
4. Activez-le (Tweak button sur *Unpause*) puis cliquez sur le bouton "Play" (Trigger DAG).
5. Observez l'arbre d'exécution (Graph View) passer progressivement au vert (Success).

## Étape 6 : Test de l'Ingestion Streaming (Kafka)
Simulez le flux de données en temps réel :
```bash
python scrapers/streaming_producer.py
```
Vérifiez les logs pour voir l'envoi des messages JSON vers le broker Kafka.

## Étape 7 : Test du Dashboard
Visualisez le résultat du travail de données :
1. Si Streamlit tourne via Docker, accédez à `http://localhost:8501`.
2. Sinon, lancez-le manuellement :
   ```bash
   streamlit run dashboards/app.py
   ```

## Étape 8 : Vérification des résultats
- Vous devez voir des statistiques agrégées sur le Dashboard.
- Le fichier `quality/quality_report.json` doit afficher un score > 0%.
- DBeaver (ou pgAdmin) branché sur `localhost:5432` doit lister vos 4 tables analytiques pleines.

## Étape 9 : Arrêt du projet
Pour éteindre l'architecture sans perdre les données :
```bash
docker-compose down
```
Pour éteindre l'architecture et supprimer les données persistantes (nettoyage total) :
```bash
docker-compose down -v
```
