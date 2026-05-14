import os
import glob
import json
import re
import logging
from typing import List, Dict, Any

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_text(text: str) -> str:
    """
    Supprime les balises HTML, nettoie les espaces inutiles et normalise le texte.
    """
    if not text:
        return ""
    # Suppression des balises HTML (approche simple via Regex)
    text_no_html = re.sub(r'<[^>]+>', '', text)
    
    # Remplacement des espaces multiples, sauts de ligne et tabulations par un seul espace
    text_normalized = re.sub(r'\s+', ' ', text_no_html)
    
    # Suppression des espaces en début et fin de chaîne
    return text_normalized.strip()


def detect_language(text: str) -> str:
    """
    Détection simple de la langue (Arabe, Français, Anglais).
    Basée sur les caractères (pour l'arabe) et les mots fréquents (pour FR/EN).
    """
    if not text:
        return "unknown"
        
    # 1. Vérification de la présence de caractères arabes
    # (la plage Unicode \u0600-\u06FF couvre les caractères arabes de base)
    if re.search(r'[\u0600-\u06FF]', text):
        return "ar"
        
    # 2. Heuristique simple pour différencier l'anglais du français
    text_lower = text.lower()
    fr_words = {'le', 'la', 'les', 'de', 'des', 'un', 'une', 'et', 'est', 'dans', 'pour'}
    en_words = {'the', 'a', 'an', 'and', 'is', 'of', 'in', 'to', 'for', 'with'}
    
    # Extraction des mots
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    fr_count = len(words.intersection(fr_words))
    en_count = len(words.intersection(en_words))
    
    if fr_count > en_count:
        return "fr"
    elif en_count > fr_count:
        return "en"
        
    return "unknown"


def remove_duplicates(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Supprime les doublons en se basant sur l'URL de l'article.
    Conserve la première occurrence rencontrée.
    """
    seen_urls = set()
    unique_articles = []
    
    for article in articles:
        url = article.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
            
    doublons_count = len(articles) - len(unique_articles)
    logging.info(f"Doublons supprimés : {doublons_count} articles retirés.")
    
    return unique_articles


def transform_bronze_to_silver(bronze_dir: str, silver_filepath: str):
    """
    Lit les fichiers de la couche Bronze, applique les traitements de nettoyage,
    et sauvegarde les données dans la couche Silver.
    """
    logging.info("--- Début de la transformation Bronze -> Silver ---")
    
    if not os.path.exists(bronze_dir):
        logging.error(f"Le dossier Bronze {bronze_dir} n'existe pas. Veuillez exécuter le scraper d'abord.")
        return
        
    # 1. Lecture de tous les fichiers JSON dans Bronze
    all_articles = []
    json_files = glob.glob(os.path.join(bronze_dir, "*.json"))
    
    if not json_files:
        logging.warning("Aucun fichier JSON trouvé dans la couche Bronze.")
        return
        
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
                all_articles.extend(articles)
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            
    logging.info(f"Lecture terminée : {len(all_articles)} articles bruts chargés depuis {len(json_files)} fichiers.")
    
    # 2. Suppression des doublons
    unique_articles = remove_duplicates(all_articles)
    
    # 3. Filtrage et Nettoyage
    silver_articles = []
    
    for article in unique_articles:
        # Vérification stricte des champs obligatoires (non nuls et non vides)
        title = article.get("title")
        content = article.get("content")
        source = article.get("source")
        url = article.get("url")
        
        if not title or not content or not source or not url:
            # On rejette la donnée si l'un de ces champs vitaux est absent
            continue
            
        # Nettoyage des textes
        cleaned_content = clean_text(content)
        cleaned_title = clean_text(title)
        
        # Ignorer si le contenu nettoyé est finalement vide
        if not cleaned_content:
            continue
            
        cleaned_author = clean_text(article.get("author", "")) if article.get("author") else None
        cleaned_category = clean_text(article.get("category", "")) if article.get("category") else None
        
        # Enrichissement : Langue et longueur du contenu
        language = detect_language(cleaned_content)
        content_length = len(cleaned_content)
        
        # Création de l'enregistrement structuré pour la couche Silver
        silver_record = {
            "title": cleaned_title,
            "author": cleaned_author,
            "publication_date": article.get("publication_date"),
            "category": cleaned_category,
            "content": cleaned_content,
            "source": source,
            "url": url,
            "scraped_at": article.get("scraped_at"),
            "language": language,
            "content_length": content_length
        }
        
        silver_articles.append(silver_record)
        
    logging.info(f"{len(silver_articles)} articles ont passé les filtres de qualité et ont été nettoyés.")
    
    # 4. Sauvegarde dans Silver
    if silver_articles:
        os.makedirs(os.path.dirname(silver_filepath), exist_ok=True)
        try:
            with open(silver_filepath, 'w', encoding='utf-8') as f:
                json.dump(silver_articles, f, ensure_ascii=False, indent=4)
            logging.info(f"Transformation réussie. Données sauvegardées dans {silver_filepath}")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde dans Silver: {e}")
    else:
        logging.warning("Aucun article à sauvegarder après le processus de nettoyage.")
        
    logging.info("--- Fin de la transformation ---")


if __name__ == "__main__":
    # Résolution dynamique des chemins
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    bronze_directory = os.path.join(project_root, "data_lake", "bronze")
    # Pour Silver, on veut rassembler les données nettoyées dans un seul fichier ou de gros batches.
    # Ici on suit la demande d'utiliser data_lake/silver/articles_silver.json
    silver_file = os.path.join(project_root, "data_lake", "silver", "articles_silver.json")
    
    transform_bronze_to_silver(bronze_directory, silver_file)
