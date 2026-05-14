import os
import json
import logging

# Configuration des logs pour le suivi de l'exécution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_quality_checks(silver_filepath: str, report_filepath: str):
    """
    Vérifie la qualité des données de la couche Silver et génère un rapport de qualité au format JSON.
    """
    logging.info("--- Début des contrôles de qualité sur la couche Silver ---")
    
    # Vérification de l'existence du fichier d'entrée
    if not os.path.exists(silver_filepath):
        logging.error(f"Le fichier Silver {silver_filepath} n'existe pas.")
        return

    # Chargement des articles nettoyés depuis la couche Silver
    try:
        with open(silver_filepath, 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier Silver : {e}")
        return

    total_articles = len(articles)
    if total_articles == 0:
        logging.warning("Aucun article trouvé dans la couche Silver.")
        return

    # Initialisation des compteurs pour chaque règle de qualité
    missing_title_count = 0
    missing_date_count = 0
    short_content_count = 0
    missing_url_count = 0
    missing_source_count = 0
    
    seen_urls = set()
    duplicate_url_count = 0
    
    # Parcours de chaque article pour vérifier les anomalies
    for article in articles:
        # Contrôle : Article sans titre
        if not article.get('title'):
            missing_title_count += 1
            
        # Contrôle : Date de publication manquante
        if not article.get('publication_date'):
            missing_date_count += 1
            
        # Contrôle : Contenu trop court (moins de 100 caractères)
        content = article.get('content', '')
        if not content or len(content) < 100:
            short_content_count += 1
            
        # Contrôle : URL manquante
        url = article.get('url')
        if not url:
            missing_url_count += 1
        else:
            # Contrôle : Doublons d'URL
            if url in seen_urls:
                duplicate_url_count += 1
            else:
                seen_urls.add(url)
                
        # Contrôle : Source manquante
        if not article.get('source'):
            missing_source_count += 1

    # Calcul du score de qualité global
    # Nous considérons comme "anomalie" chaque défaut trouvé.
    total_anomalies = (
        missing_title_count + 
        missing_date_count + 
        short_content_count + 
        missing_url_count + 
        missing_source_count + 
        duplicate_url_count
    )
    
    # Le nombre total de contrôles effectués correspond à 6 règles par article
    total_checks = total_articles * 6
    
    # Le score global est le pourcentage de tests passés avec succès
    global_quality_score = ((total_checks - total_anomalies) / total_checks) * 100 if total_checks > 0 else 0.0

    # Création de la structure du rapport
    report = {
        "total_articles": total_articles,
        "missing_title_count": missing_title_count,
        "missing_date_count": missing_date_count,
        "short_content_count": short_content_count,
        "missing_url_count": missing_url_count,
        "missing_source_count": missing_source_count,
        "duplicate_url_count": duplicate_url_count,
        "global_quality_score": round(global_quality_score, 2)
    }

    # Sauvegarde du rapport au format JSON dans le dossier spécifié
    os.makedirs(os.path.dirname(report_filepath), exist_ok=True)
    try:
        with open(report_filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        logging.info(f"Rapport de qualité généré avec succès : {report_filepath}")
        logging.info(f"Score de qualité global : {round(global_quality_score, 2)}%")
    except Exception as e:
        logging.error(f"Erreur lors de l'enregistrement du rapport de qualité : {e}")

    logging.info("--- Fin des contrôles de qualité ---")

if __name__ == "__main__":
    # Résolution des chemins absolus pour exécuter le script depuis n'importe où
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Chemins vers les fichiers d'entrée et de sortie
    silver_file = os.path.join(project_root, "data_lake", "silver", "articles_silver.json")
    report_file = os.path.join(current_dir, "quality_report.json")
    
    # Lancement de l'analyse
    run_quality_checks(silver_file, report_file)
