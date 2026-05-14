import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

# Configuration des logs pour avoir un suivi détaillé du scraper
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_article_record(
    title: Optional[str],
    author: Optional[str],
    publication_date: Optional[str],
    category: Optional[str],
    content: Optional[str],
    source: str,
    url: str
) -> Dict[str, Any]:
    """
    Crée un dictionnaire standard pour un article.
    Les champs manquants sont conservés comme None (qui sera converti en null en JSON).
    """
    return {
        "title": title,
        "author": author,
        "publication_date": publication_date,
        "category": category,
        "content": content,
        "source": source,
        "url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }

def fetch_html(url: str) -> Optional[BeautifulSoup]:
    """
    Récupère le contenu HTML d'une URL de manière robuste.
    """
    try:
        # Ajout d'un User-Agent pour simuler un navigateur et éviter certains blocages
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (ex: 404, 500)
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la récupération de l'URL {url}: {e}")
        return None

def save_to_bronze(articles: List[Dict[str, Any]], bronze_dir: str):
    """
    Sauvegarde la liste d'articles dans un fichier JSON dans la zone Bronze.
    Génère un nouveau fichier horodaté à chaque exécution.
    """
    if not articles:
        logging.info("Aucun article à sauvegarder.")
        return

    # S'assurer que le dossier bronze existe
    os.makedirs(bronze_dir, exist_ok=True)
    
    # Générer le nom de fichier horodaté (ex: articles_bronze_2026_05_13_10_00.json)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    filename = f"articles_bronze_{timestamp}.json"
    filepath = os.path.join(bronze_dir, filename)

    # Écriture dans le fichier (nouvelle sauvegarde à chaque fois)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
        logging.info(f"Sauvegarde réussie : {len(articles)} articles enregistrés dans le fichier {filename}.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde dans le fichier JSON : {e}")


def scrape_hespress() -> List[Dict[str, Any]]:
    """
    Scraper spécifique pour le site d'actualités Hespress.
    """
    logging.info("Démarrage du scraping Hespress...")
    base_url = "https://www.hespress.com"
    soup = fetch_html(base_url)
    articles_data = []

    if not soup:
        return articles_data

    try:
        # Note : Les sélecteurs CSS (classes) doivent être adaptés à la structure HTML réelle du site.
        # Ici, une structure générique probable est proposée.
        article_cards = soup.find_all('div', class_='card') 
        
        # Limite aux 5 premiers articles pour l'exemple
        for card in article_cards[:5]:
            try:
                link_tag = card.find('a')
                if not link_tag:
                    continue
                    
                url = link_tag.get('href')
                if not url.startswith('http'):
                    url = base_url + url
                    
                title = link_tag.get('title') or (link_tag.text.strip() if link_tag else None)
                
                # Visiter la page de l'article pour récupérer les détails
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                
                # Extraction des champs avec tolérance (None si introuvable)
                author_tag = article_soup.find('span', class_='author-name')
                author = author_tag.text.strip() if author_tag else None
                
                date_tag = article_soup.find('span', class_='date-post')
                pub_date = date_tag.text.strip() if date_tag else None
                
                cat_tag = article_soup.find('a', class_='cat')
                category = cat_tag.text.strip() if cat_tag else None
                
                content_div = article_soup.find('div', class_='article-content')
                content = content_div.text.strip() if content_div else None
                
                record = create_article_record(
                    title=title,
                    author=author,
                    publication_date=pub_date,
                    category=category,
                    content=content,
                    source="Hespress",
                    url=url
                )
                articles_data.append(record)
            except Exception as e:
                logging.warning(f"Erreur lors du traitement d'un article Hespress: {e}")
                
    except Exception as e:
        logging.error(f"Erreur globale lors du scraping Hespress: {e}")

    return articles_data


def scrape_bbc() -> List[Dict[str, Any]]:
    """
    Scraper spécifique pour le site de BBC News.
    """
    logging.info("Démarrage du scraping BBC...")
    base_url = "https://www.bbc.com/news"
    soup = fetch_html(base_url)
    articles_data = []

    if not soup:
        return articles_data

    try:
        # Extraction générique des liens d'articles
        article_links = soup.find_all('a', attrs={'data-testid': 'internal-link'}) 
        
        processed_urls = set()
        
        for link_tag in article_links:
            if len(processed_urls) >= 5: # Limite à 5 articles pour l'exemple
                break
                
            try:
                url = link_tag.get('href')
                # Ignorer les liens qui ne sont pas des articles d'actualité
                if not url or '/news/' not in url:
                    continue
                    
                if not url.startswith('http'):
                    url = "https://www.bbc.com" + url
                    
                # Éviter de scraper la même URL plusieurs fois
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                    
                title_tag = link_tag.find(['h1', 'h2', 'h3', 'span'])
                title = title_tag.text.strip() if title_tag else None
                
                # Visiter la page de l'article
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                    
                # Extraction des informations de l'article
                author_tag = article_soup.find('div', class_='ssrcss-68pt20-Text-TextContributorName')
                author = author_tag.text.strip() if author_tag else None
                
                date_tag = article_soup.find('time')
                pub_date = date_tag.get('datetime') if date_tag else None
                
                # On essaie d'extraire la catégorie de l'URL si possible
                url_parts = url.split('/')
                category = url_parts[4] if len(url_parts) > 4 else None
                
                # Le contenu de la BBC est souvent découpé en plusieurs blocs
                content_blocks = article_soup.find_all('div', attrs={'data-component': 'text-block'})
                content = " ".join([block.text.strip() for block in content_blocks]) if content_blocks else None
                
                record = create_article_record(
                    title=title,
                    author=author,
                    publication_date=pub_date,
                    category=category,
                    content=content,
                    source="BBC",
                    url=url
                )
                articles_data.append(record)
            except Exception as e:
                logging.warning(f"Erreur lors du traitement d'un article BBC: {e}")
                
    except Exception as e:
        logging.error(f"Erreur globale lors du scraping BBC: {e}")

    return articles_data


if __name__ == "__main__":
    # Déduction automatique du chemin absolu pour le fichier JSON cible
    # Cela permet d'exécuter le script depuis n'importe quel dossier
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    bronze_dir = os.path.join(project_root, "data_lake", "bronze")
    
    logging.info("--- Début du pipeline de scraping batch ---")
    
    all_collected_articles = []
    
    # 1. Scraping Hespress
    hespress_data = scrape_hespress()
    all_collected_articles.extend(hespress_data)
    
    # 2. Scraping BBC
    bbc_data = scrape_bbc()
    all_collected_articles.extend(bbc_data)
    
    # 3. Sauvegarde dans la zone Bronze
    save_to_bronze(all_collected_articles, bronze_dir=bronze_dir)
    
    logging.info("--- Fin du pipeline de scraping batch ---")
