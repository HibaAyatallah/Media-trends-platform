import os
import json
import logging
import re
from collections import Counter
import pandas as pd

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Liste basique de stopwords (mots vides) en français et anglais
STOPWORDS = {
    # Français
    'dans', 'pour', 'avec', 'plus', 'cette', 'fait', 'tout', 'comme', 'être',
    'avoir', 'sont', 'faire', 'aussi', 'bien', 'peut', 'très', 'tous', 'mais',
    'nous', 'vous', 'leur', 'sans', 'dont', 'quand', 'après', 'alors', 'nous',
    'entre', 'encore', 'contre', 'depuis', 'ceux', 'cela', 'sous', 'vers',
    # Anglais
    'that', 'with', 'this', 'from', 'they', 'have', 'were', 'what', 'about',
    'their', 'would', 'will', 'there', 'which', 'when', 'make', 'more', 'some',
    'also', 'other', 'could', 'such', 'than', 'because', 'over', 'into', 'only',
    'after', 'before', 'most', 'through', 'where', 'much', 'should', 'been'
}

def extract_keywords(df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    """
    Extrait les mots-clés les plus fréquents à partir des contenus et titres des articles.
    Ignore les mots très courts (moins de 4 lettres) et une liste basique de stopwords.
    """
    logging.info("Extraction des mots-clés en cours...")
    
    # On rassemble tous les textes disponibles (titre + contenu)
    all_text = ""
    for _, row in df.iterrows():
        title = str(row.get('title', ''))
        content = str(row.get('content', ''))
        all_text += f" {title} {content}"
        
    # Mise en minuscule globale
    all_text_lower = all_text.lower()
    
    # Extraction des mots contenant uniquement des lettres (dont accentuées) 
    # et ayant au moins 4 caractères
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', all_text_lower)
    
    # Filtrage pour retirer les stopwords
    filtered_words = [w for w in words if w not in STOPWORDS]
    
    # Comptage des fréquences
    word_counts = Counter(filtered_words)
    
    # Récupération du top N
    top_words = word_counts.most_common(top_n)
    
    # Conversion en DataFrame
    keywords_df = pd.DataFrame(top_words, columns=['keyword', 'frequency'])
    
    return keywords_df


def transform_silver_to_gold(silver_filepath: str, gold_dir: str):
    """
    Lit les données nettoyées de la couche Silver, réalise des agrégations
    analytiques avec pandas, et génère des tables CSV dans la couche Gold.
    """
    logging.info("--- Début de la transformation Silver -> Gold ---")
    
    # 1. Vérification du fichier d'entrée
    if not os.path.exists(silver_filepath):
        logging.error(f"Le fichier Silver {silver_filepath} n'existe pas. Veuillez exécuter le script bronze_to_silver.py d'abord.")
        return
        
    # 2. Création du répertoire de destination
    os.makedirs(gold_dir, exist_ok=True)
    
    # 3. Chargement des données dans un DataFrame pandas
    try:
        df = pd.read_json(silver_filepath)
        logging.info(f"Chargement réussi : {len(df)} articles trouvés dans Silver.")
    except Exception as e:
        logging.error(f"Erreur lors du chargement du fichier JSON Silver avec pandas: {e}")
        return
        
    if df.empty:
        logging.warning("Le DataFrame Silver est vide, aucune table Gold ne sera générée.")
        return

    # ------------- Génération des tables Gold -------------

    # Table 1 : articles_by_source.csv
    logging.info("Génération de articles_by_source.csv...")
    if 'source' in df.columns:
        df_source = df.groupby('source').size().reset_index(name='number_of_articles')
    else:
        df_source = pd.DataFrame(columns=['source', 'number_of_articles'])
    
    df_source.to_csv(os.path.join(gold_dir, "articles_by_source.csv"), index=False, encoding='utf-8')

    # Table 2 : articles_by_day.csv
    logging.info("Génération de articles_by_day.csv...")
    if 'publication_date' in df.columns:
        # Nettoyage rapide pour ne garder que la date YYYY-MM-DD
        df['pub_day'] = df['publication_date'].astype(str).apply(
            lambda x: x[:10] if x and str(x).lower() not in ['none', 'nan', ''] else 'Unknown'
        )
    else:
        df['pub_day'] = 'Unknown'
        
    df_day = df.groupby('pub_day').size().reset_index(name='number_of_articles')
    df_day.rename(columns={'pub_day': 'publication_date'}, inplace=True)
    df_day.to_csv(os.path.join(gold_dir, "articles_by_day.csv"), index=False, encoding='utf-8')

    # Table 3 : articles_by_category.csv
    logging.info("Génération de articles_by_category.csv...")
    if 'category' in df.columns:
        # Remplacer les valeurs nulles par "Unknown" ou "Non catégorisé"
        df['category_clean'] = df['category'].fillna('Unknown')
    else:
        df['category_clean'] = 'Unknown'
        
    df_category = df.groupby('category_clean').size().reset_index(name='number_of_articles')
    df_category.rename(columns={'category_clean': 'category'}, inplace=True)
    df_category.to_csv(os.path.join(gold_dir, "articles_by_category.csv"), index=False, encoding='utf-8')

    # Table 4 : top_keywords.csv
    logging.info("Génération de top_keywords.csv...")
    df_keywords = extract_keywords(df, top_n=100)
    df_keywords.to_csv(os.path.join(gold_dir, "top_keywords.csv"), index=False, encoding='utf-8')

    logging.info(f"Toutes les tables Gold ont été générées et sauvegardées avec succès dans {gold_dir}")
    logging.info("--- Fin de la transformation Silver -> Gold ---")


if __name__ == "__main__":
    # Déduction dynamique des chemins
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    silver_file = os.path.join(project_root, "data_lake", "silver", "articles_silver.json")
    gold_directory = os.path.join(project_root, "data_lake", "gold")
    
    transform_silver_to_gold(silver_file, gold_directory)
