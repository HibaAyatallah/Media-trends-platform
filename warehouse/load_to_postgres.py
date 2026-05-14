import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Configuration des logs pour un suivi détaillé
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_engine():
    """
    Construit la chaîne de connexion et crée un moteur SQLAlchemy connecté à PostgreSQL.
    Les informations de connexion sont récupérées depuis les variables d'environnement.
    """
    # Récupération des variables d'environnement avec des valeurs par défaut pour le développement
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'mediatrends')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')

    # Format de la chaîne de connexion SQLAlchemy : postgresql://user:password@host:port/database
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    try:
        engine = create_engine(connection_string)
        # On tente une connexion pour valider que la base de données est accessible
        with engine.connect() as connection:
            logging.info(f"Connexion réussie à la base de données PostgreSQL sur {host}:{port}")
        return engine
    except SQLAlchemyError as e:
        logging.error(f"Erreur fatale de connexion à la base de données : {e}")
        return None

def load_csv_to_table(engine, csv_path: str, table_name: str):
    """
    Lit un fichier CSV pandas et utilise to_sql pour insérer les données en base.
    On utilise if_exists='replace' car les tables d'agrégation Gold sont généralement 
    recalculées complètement à chaque passage du pipeline batch.
    """
    if not os.path.exists(csv_path):
        logging.warning(f"Le fichier {csv_path} est introuvable. Chargement ignoré pour la table {table_name}.")
        return

    try:
        # Lecture des données Gold
        df = pd.read_csv(csv_path)
        
        if df.empty:
            logging.warning(f"Le fichier {os.path.basename(csv_path)} est vide. Aucune donnée insérée.")
            return
            
        logging.info(f"Chargement de {len(df)} lignes de {os.path.basename(csv_path)} vers la table '{table_name}'...")
        
        # Insertion des données dans PostgreSQL. 
        # index=False évite de créer une colonne inutile pour l'index du DataFrame.
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        logging.info(f"Succès : Les données ont été chargées dans la table '{table_name}'.")
        
    except Exception as e:
        logging.error(f"Erreur lors du chargement des données vers {table_name} : {e}")

if __name__ == "__main__":
    logging.info("--- Début de l'ingestion des données Gold vers PostgreSQL ---")
    
    # Résolution dynamique des chemins vers la zone Gold
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    gold_dir = os.path.join(project_root, "data_lake", "gold")
    
    # 1. Obtenir le moteur SQLAlchemy (connexion BDD)
    db_engine = get_db_engine()
    
    if db_engine:
        # 2. Définir le mapping entre les fichiers CSV cibles et les noms des tables
        files_to_load = {
            "articles_by_source.csv": "agg_articles_by_source",
            "articles_by_day.csv": "agg_articles_by_day",
            "top_keywords.csv": "agg_top_keywords",
            "articles_by_category.csv": "agg_articles_by_category" 
        }
        
        # 3. Charger chaque fichier itérativement
        for filename, table_name in files_to_load.items():
            csv_path = os.path.join(gold_dir, filename)
            load_csv_to_table(db_engine, csv_path, table_name)
            
    logging.info("--- Fin de l'ingestion des données vers PostgreSQL ---")
