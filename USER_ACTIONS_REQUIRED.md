# Actions Requises de l'Utilisateur (USER_ACTIONS_REQUIRED)

Ce document liste toutes les actions que vous devez réaliser manuellement sur votre machine pour exécuter le projet "Media Trends Platform".

## 1. Prérequis Système

### Installer Python
- **Ce que je dois faire** : Installer Python 3.9 ou supérieur.
- **Pourquoi c'est nécessaire** : Le projet est écrit en Python. Même si Docker est utilisé, Python en local est indispensable pour tester les scripts manuellement.
- **La commande exacte** : Téléchargez depuis `python.org` ou utilisez `winget install Python.Python.3.11`.
- **Résultat attendu** : `python --version` retourne la bonne version.
- **Erreurs possibles** : Python n'est pas dans le PATH.
- **Comment corriger** : Cochez "Add Python to PATH" lors de l'installation sous Windows.

### Installer Docker Desktop
- **Ce que je dois faire** : Installer Docker Desktop (Windows/Mac) ou Docker Engine (Linux).
- **Pourquoi c'est nécessaire** : Héberge tous les services (PostgreSQL, Kafka, Airflow, etc.).
- **La commande exacte** : Téléchargez depuis `docker.com`.
- **Résultat attendu** : `docker --version` retourne la version de Docker.

### Installer Git
- **Ce que je dois faire** : Installer Git.
- **Pourquoi c'est nécessaire** : Pour cloner et gérer le code source du projet.
- **La commande exacte** : `winget install Git.Git` ou téléchargement classique.
- **Résultat attendu** : `git --version` fonctionne.

## 2. Lancement de l'Infrastructure

### Vérifier que Docker est lancé
- **Ce que je dois faire** : Ouvrir l'application Docker Desktop.
- **Pourquoi c'est nécessaire** : `docker-compose` a besoin du démon Docker actif.
- **La commande exacte** : `docker info`
- **Erreurs possibles** : "error during connect".
- **Comment corriger** : Démarrez l'application Docker Desktop et attendez que l'icône devienne verte.

### Créer ou vérifier le fichier .env
- **Ce que je dois faire** : Créer un fichier `.env` à la racine (optionnel, les valeurs par défaut sont codées en dur pour la simplicité académique).
- **Pourquoi c'est nécessaire** : Sécurise les mots de passe.
- **La commande exacte** : Créez un fichier `.env` avec `POSTGRES_USER=postgres` etc.

### Lancer docker-compose
- **Ce que je dois faire** : Lancer tous les conteneurs.
- **Pourquoi c'est nécessaire** : Initialise la base de données, le bus de message et l'orchestrateur.
- **La commande exacte** : `docker-compose up -d`
- **Résultat attendu** : Tous les conteneurs affichent `Started`.
- **Erreurs possibles** : Port 5432 ou 8080 déjà utilisé.
- **Comment corriger** : Arrêtez les applications locales qui utilisent ces ports.

## 3. Vérification des Services

### Vérifier PostgreSQL
- **La commande exacte** : `docker ps | findstr postgres` (Windows) ou accès via un client lourd comme DBeaver (sur `localhost:5432`).

### Vérifier MinIO
- **La commande exacte** : Ouvrez un navigateur sur `http://localhost:9001` (admin / adminpassword).

### Vérifier Kafka
- **La commande exacte** : `docker logs media_kafka`.

### Vérifier Airflow
- **La commande exacte** : Ouvrez un navigateur sur `http://localhost:8080` (admin / admin).

### Vérifier Streamlit
- **La commande exacte** : Ouvrez un navigateur sur `http://localhost:8501`.

## 4. Tests Manuels du Pipeline

Pour exécuter ces tests, installez d'abord les dépendances : `pip install -r requirements.txt`.

### Tester le scraper batch
- **La commande exacte** : `python scrapers/batch_scraper.py`
- **Résultat attendu** : Un fichier JSON apparaît dans `data_lake/bronze/`.

### Tester Bronze vers Silver
- **La commande exacte** : `python transformations/bronze_to_silver.py`
- **Résultat attendu** : Création de `data_lake/silver/articles_silver.json`.

### Tester Silver vers Gold
- **La commande exacte** : `python transformations/silver_to_gold.py`
- **Résultat attendu** : Création de 4 fichiers CSV dans `data_lake/gold/`.

### Tester le rapport qualité
- **La commande exacte** : `python quality/data_quality_checks.py`
- **Résultat attendu** : Fichier `quality_report.json` créé dans `quality/`.

### Tester le chargement PostgreSQL
- **La commande exacte** : `python warehouse/load_to_postgres.py`
- **Résultat attendu** : Les données CSV sont insérées dans les tables PostgreSQL.

### Tester le dashboard
- **La commande exacte** : `streamlit run dashboards/app.py`
- **Résultat attendu** : Le dashboard s'ouvre dans le navigateur avec des graphiques remplis.

## 5. Arrêt des Services

### Arrêter les services
- **Ce que je dois faire** : Éteindre l'infrastructure proprement.
- **La commande exacte** : `docker-compose down`
- **Pourquoi c'est nécessaire** : Libère la RAM et le CPU de votre machine tout en conservant les données dans les volumes.
