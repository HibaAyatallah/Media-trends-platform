# Media Trends Platform : Analyse et Ingénierie des Données Médiatiques

## 1. Présentation du projet
**Media Trends Platform** est une architecture Big Data de bout en bout conçue pour la collecte, le traitement, l'analyse et la restitution des tendances médiatiques mondiales. Ce projet illustre la conception d'un pipeline de données robuste, intégrant à la fois des flux batch et streaming, afin d'extraire des insights stratégiques à partir d'articles d'actualité.

## 2. Objectifs
- **Automatisation de l'Ingestion** : Collecter massivement des articles d'actualités provenant de diverses sources.
- **Fiabilité et Standardisation** : Mettre en place une architecture Medallion (Data Lakehouse) pour structurer progressivement la donnée.
- **Garantie de la Qualité** : Appliquer des tests rigoureux (Data Quality Checks) pour prévenir la propagation d'anomalies.
- **Restitution Analytique** : Modéliser les données pour l'aide à la décision à travers des tableaux de bord interactifs.
- **Orchestration** : Planifier et superviser l'ensemble des processus ETL avec Apache Airflow.

## 3. Architecture globale
L'architecture du système s'articule autour du paradigme moderne **Data Lakehouse**, associant la flexibilité d'un Data Lake (MinIO/Système de fichiers local) à la structure transactionnelle d'un Data Warehouse (PostgreSQL). L'intégralité des flux est orchestrée par Airflow et isolée de manière reproductible via la conteneurisation Docker.

## 4. Technologies utilisées
- **Langage** : Python 3.9+ (Pandas, BeautifulSoup)
- **Ingestion Streaming** : Apache Kafka, Zookeeper, `kafka-python`
- **Orchestration** : Apache Airflow
- **Data Lake** : MinIO (compatible S3) / Stockage local hiérarchisé
- **Data Warehouse** : PostgreSQL, SQLAlchemy, Psycopg2
- **Visualisation** : Streamlit, Plotly
- **Conteneurisation** : Docker, Docker Compose

## 5. Structure du projet
```text
media-trends-platform/
├── airflow/            # DAGs et configuration de l'orchestrateur Apache Airflow
├── dashboards/         # Code de l'application de restitution visuelle (Streamlit)
├── data_lake/          # Zones de stockage hiérarchisées (bronze, silver, gold)
├── quality/            # Scripts de validation et scoring de la qualité de la donnée
├── scrapers/           # Moteurs de collecte (Batch Scraper & Kafka Streaming)
├── transformations/    # Scripts de traitement ETL (Bronze -> Silver, Silver -> Gold)
├── warehouse/          # Schémas SQL et scripts de chargement vers la BDD
├── docker-compose.yml  # Déploiement de l'infrastructure
└── requirements.txt    # Dépendances Python du projet
```

## 6. Description du pipeline

### Sources de données
Les données sont extraites de grands portails d'actualités (ex: Hespress, BBC), offrant une couverture sémantique hétérogène (titres, auteurs, contenus textuels, catégories de l'article).

### Ingestion
- **Batch** : Exécution périodique de scripts de scraping (`batch_scraper.py`) récupérant le stock récent d'articles.
- **Streaming** : Publication en temps réel (`streaming_producer.py`) des événements liés aux nouveaux articles vers un topic Kafka `news_articles`.

### Data Lake (Architecture Medallion)
- **Couche Bronze** : Zone d'atterrissage (*Landing Zone*). Les données sont stockées au format JSON brut, exactement telles qu'ingérées, avec leur timestamp de collecte.
- **Couche Silver** : Zone de conformation. Les données brutes sont nettoyées (retrait des stopwords, homogénéisation des champs, formatage des dates) et converties en entités structurées de haute qualité.
- **Couche Gold** : Zone analytique. Les données sont pré-agrégées selon des axes d'analyse précis (volumétrie par source, par jour, extraction des mots-clés fréquents) et sauvegardées au format CSV.

### Data Warehouse
Les agrégations issues de la couche Gold sont ingérées (`load_to_postgres.py`) dans un Data Warehouse hébergé sur **PostgreSQL**. Ce schéma relationnel (`schema.sql`) sépare les données via des tables de faits (`fact_articles`) et des tables de dimensions (`dim_source`, `dim_category`) permettant des requêtes BI performantes.

### Dashboard
Une interface Web analytique développée avec **Streamlit** se connecte au Data Warehouse (ou lit directement la zone Gold) pour offrir une vue macroscopique dynamique : KPIs, graphiques interactifs (Plotly) et filtres multi-critères temps réel.

## 7. Qualité des données
Le module `quality/data_quality_checks.py` constitue une porte de qualité critique (*Quality Gate*). Il valide la couche Silver avant la phase analytique en contrôlant :
- **La complétude** : présence obligatoire de l'URL, du titre et de la source.
- **La validité** : longueur minimale du contenu textuel.
- **L'unicité** : absence de doublons basés sur l'URL de l'article.
Un rapport de qualité est généré au format JSON avec un score global, permettant le blocage du pipeline en cas de dégradation critique des données.

## 8. Gouvernance
Le pipeline assure une stricte traçabilité. Chaque donnée se voit attribuer un timestamp d'ingestion (`scraped_at`). L'approche Medallion garantit l'immuabilité : il est toujours possible de remonter de la donnée agrégée (Gold) à la source initiale (Bronze) pour un rejeu (*reprocessing*) complet de l'historique sans perte d'information.

## 9. Installation avec Docker
L'ensemble de l'écosystème est packagé. Pour initier le projet :

```bash
# 1. Placez-vous à la racine du projet
cd media-trends-platform

# 2. Démarrez l'infrastructure complète en arrière-plan
docker-compose up -d
```
Les conteneurs montés incluront : PostgreSQL, MinIO, Zookeeper, Kafka, Airflow (Webserver, Scheduler, Init) et l'interface Streamlit.

## 10. Commandes pour exécuter le projet
Une fois l'infrastructure démarrée :
- **Orchestration Airflow** : Accédez à `http://localhost:8080` (Identifiants : `admin` / `admin`). Activez le DAG `media_trends_pipeline` pour lancer le traitement automatique complet.
- **Interface Streamlit** : Accédez à `http://localhost:8501` pour explorer le Dashboard en direct.
- **Simulation Streaming** : Lancez localement `python scrapers/streaming_producer.py` pour envoyer artificiellement des articles dans le flux Kafka.

## 11. Résultats attendus
- Constitution automatisée et pérenne d'un Data Lake analytique enrichi jour après jour.
- Visualisation instantanée et interactive des parts de voix médiatiques (répartition par source, par catégorie).
- Identification rapide des macro-tendances (*Top Keywords*) permettant d'orienter les stratégies de veille.

## 12. Améliorations futures
- **Intelligence Artificielle** : Intégration de modèles NLP avancés (LLMs, BERT) pour l'analyse de sentiment automatisée et le résumé exécutif des articles.
- **Stockage Cloud** : Migration complète de la zone de stockage locale vers S3 (via le service MinIO déjà pré-installé) en utilisant `boto3`.
- **Real-Time Processing** : Remplacement du batching Python par une intégration Apache Spark Streaming ou Apache Flink pour consommer le topic Kafka et rafraîchir les KPI instantanément.
