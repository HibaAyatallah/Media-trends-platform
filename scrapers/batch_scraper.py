import json
import logging
import os
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def create_article_record(title, author, publication_date, category, content, source, url):
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
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur fetch {url}: {e}")
        return None

def save_to_bronze(articles: List[Dict[str, Any]], bronze_dir: str):
    if not articles:
        logging.info("Aucun article à sauvegarder.")
        return
    os.makedirs(bronze_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    filename = f"articles_bronze_{timestamp}.json"
    filepath = os.path.join(bronze_dir, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
        logging.info(f"Sauvegarde réussie : {len(articles)} articles → {filename}")
    except Exception as e:
        logging.error(f"Erreur sauvegarde : {e}")


def scrape_hespress() -> List[Dict[str, Any]]:
    logging.info("Scraping Hespress...")
    base_url = "https://www.hespress.com"
    soup = fetch_html(base_url)
    articles_data = []
    if not soup:
        return articles_data
    try:
        article_cards = soup.find_all('div', class_='card')
        for card in article_cards[:10]:
            try:
                link_tag = card.find('a')
                if not link_tag:
                    continue
                url = link_tag.get('href')
                if not url or not url.startswith('http'):
                    url = base_url + url
                title = link_tag.get('title') or link_tag.text.strip()
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                author_tag = article_soup.find('span', class_='author-name')
                author = author_tag.text.strip() if author_tag else None
                date_tag = article_soup.find('span', class_='date-post')
                pub_date = date_tag.text.strip() if date_tag else None
                cat_tag = article_soup.find('a', class_='cat')
                category = cat_tag.text.strip() if cat_tag else None
                content_div = article_soup.find('div', class_='article-content')
                content = content_div.text.strip() if content_div else None
                articles_data.append(create_article_record(title, author, pub_date, category, content, "Hespress", url))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.warning(f"Erreur article Hespress: {e}")
    except Exception as e:
        logging.error(f"Erreur globale Hespress: {e}")
    logging.info(f"Hespress : {len(articles_data)} articles collectés")
    return articles_data


def scrape_bbc() -> List[Dict[str, Any]]:
    logging.info("Scraping BBC...")
    base_url = "https://www.bbc.com/news"
    soup = fetch_html(base_url)
    articles_data = []
    if not soup:
        return articles_data
    try:
        article_links = soup.find_all('a', attrs={'data-testid': 'internal-link'})
        processed_urls = set()
        for link_tag in article_links:
            if len(processed_urls) >= 10:
                break
            try:
                url = link_tag.get('href')
                if not url or '/news/' not in url:
                    continue
                if not url.startswith('http'):
                    url = "https://www.bbc.com" + url
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                title_tag = link_tag.find(['h1', 'h2', 'h3', 'span'])
                title = title_tag.text.strip() if title_tag else None
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                author_tag = article_soup.find('div', class_='ssrcss-68pt20-Text-TextContributorName')
                author = author_tag.text.strip() if author_tag else None
                date_tag = article_soup.find('time')
                pub_date = date_tag.get('datetime') if date_tag else None
                url_parts = url.split('/')
                category = url_parts[4] if len(url_parts) > 4 else None
                content_blocks = article_soup.find_all('div', attrs={'data-component': 'text-block'})
                content = " ".join([b.text.strip() for b in content_blocks]) if content_blocks else None
                articles_data.append(create_article_record(title, author, pub_date, category, content, "BBC", url))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.warning(f"Erreur article BBC: {e}")
    except Exception as e:
        logging.error(f"Erreur globale BBC: {e}")
    logging.info(f"BBC : {len(articles_data)} articles collectés")
    return articles_data


def scrape_aljazeera() -> List[Dict[str, Any]]:
    logging.info("Scraping Al Jazeera...")
    base_url = "https://www.aljazeera.com/news/"
    soup = fetch_html(base_url)
    articles_data = []
    if not soup:
        return articles_data
    try:
        article_links = soup.find_all('a', class_='u-clickable-card__link')
        processed_urls = set()
        for link_tag in article_links:
            if len(processed_urls) >= 10:
                break
            try:
                url = link_tag.get('href')
                if not url:
                    continue
                if not url.startswith('http'):
                    url = "https://www.aljazeera.com" + url
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                title_tag = article_soup.find('h1')
                title = title_tag.text.strip() if title_tag else None
                author_tag = article_soup.find('a', class_='article-author-name')
                author = author_tag.text.strip() if author_tag else None
                date_tag = article_soup.find('time')
                pub_date = date_tag.get('datetime') if date_tag else None
                cat_tag = article_soup.find('a', class_='article-heading__category')
                category = cat_tag.text.strip() if cat_tag else "News"
                content_div = article_soup.find('div', class_='wysiwyg')
                content = content_div.text.strip() if content_div else None
                if title:
                    articles_data.append(create_article_record(title, author, pub_date, category, content, "Al Jazeera", url))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.warning(f"Erreur article Al Jazeera: {e}")
    except Exception as e:
        logging.error(f"Erreur globale Al Jazeera: {e}")
    logging.info(f"Al Jazeera : {len(articles_data)} articles collectés")
    return articles_data


def scrape_reuters() -> List[Dict[str, Any]]:
    logging.info("Scraping Reuters...")
    base_url = "https://www.reuters.com/world/"
    soup = fetch_html(base_url)
    articles_data = []
    if not soup:
        return articles_data
    try:
        article_links = soup.find_all('a', attrs={'data-testid': 'Heading'})
        processed_urls = set()
        for link_tag in article_links:
            if len(processed_urls) >= 10:
                break
            try:
                url = link_tag.get('href')
                if not url:
                    continue
                if not url.startswith('http'):
                    url = "https://www.reuters.com" + url
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                title = link_tag.text.strip()
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                author_tag = article_soup.find('a', attrs={'rel': 'author'})
                author = author_tag.text.strip() if author_tag else None
                date_tag = article_soup.find('time')
                pub_date = date_tag.get('datetime') if date_tag else None
                category = "World"
                content_div = article_soup.find('div', class_='article-body__content')
                content = content_div.text.strip() if content_div else None
                if title:
                    articles_data.append(create_article_record(title, author, pub_date, category, content, "Reuters", url))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.warning(f"Erreur article Reuters: {e}")
    except Exception as e:
        logging.error(f"Erreur globale Reuters: {e}")
    logging.info(f"Reuters : {len(articles_data)} articles collectés")
    return articles_data


def scrape_cnn() -> List[Dict[str, Any]]:
    logging.info("Scraping CNN...")
    base_url = "https://edition.cnn.com/world"
    soup = fetch_html(base_url)
    articles_data = []
    if not soup:
        return articles_data
    try:
        article_links = soup.find_all('a', class_='container__link')
        processed_urls = set()
        for link_tag in article_links:
            if len(processed_urls) >= 10:
                break
            try:
                url = link_tag.get('href')
                if not url or '/videos/' in url:
                    continue
                if not url.startswith('http'):
                    url = "https://edition.cnn.com" + url
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                title_tag = article_soup.find('h1')
                title = title_tag.text.strip() if title_tag else None
                author_tag = article_soup.find('span', class_='byline__name')
                author = author_tag.text.strip() if author_tag else None
                date_tag = article_soup.find('div', class_='timestamp')
                pub_date = date_tag.text.strip() if date_tag else None
                category = "World"
                content_div = article_soup.find('div', class_='article__content')
                content = content_div.text.strip() if content_div else None
                if title:
                    articles_data.append(create_article_record(title, author, pub_date, category, content, "CNN", url))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.warning(f"Erreur article CNN: {e}")
    except Exception as e:
        logging.error(f"Erreur globale CNN: {e}")
    logging.info(f"CNN : {len(articles_data)} articles collectés")
    return articles_data


def scrape_akhbarona() -> List[Dict[str, Any]]:
    logging.info("Scraping Akhbarona...")
    base_url = "https://www.akhbarona.com"
    soup = fetch_html(base_url)
    articles_data = []
    if not soup:
        return articles_data
    try:
        article_links = soup.find_all('a', class_='title')
        processed_urls = set()
        for link_tag in article_links:
            if len(processed_urls) >= 10:
                break
            try:
                url = link_tag.get('href')
                if not url:
                    continue
                if not url.startswith('http'):
                    url = base_url + url
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                title = link_tag.text.strip()
                article_soup = fetch_html(url)
                if not article_soup:
                    continue
                date_tag = article_soup.find('span', class_='date')
                pub_date = date_tag.text.strip() if date_tag else None
                cat_tag = article_soup.find('a', class_='category')
                category = cat_tag.text.strip() if cat_tag else None
                content_div = article_soup.find('div', class_='article-body')
                content = content_div.text.strip() if content_div else None
                if title:
                    articles_data.append(create_article_record(title, None, pub_date, category, content, "Akhbarona", url))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.warning(f"Erreur article Akhbarona: {e}")
    except Exception as e:
        logging.error(f"Erreur globale Akhbarona: {e}")
    logging.info(f"Akhbarona : {len(articles_data)} articles collectés")
    return articles_data


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    bronze_dir = os.path.join(project_root, "data_lake", "bronze")

    logging.info("--- Début du pipeline de scraping batch ---")
    all_articles = []

    all_articles.extend(scrape_hespress())
    all_articles.extend(scrape_bbc())
    all_articles.extend(scrape_aljazeera())
    all_articles.extend(scrape_reuters())
    all_articles.extend(scrape_cnn())
    all_articles.extend(scrape_akhbarona())

    save_to_bronze(all_articles, bronze_dir=bronze_dir)
    logging.info(f"--- Fin du scraping : {len(all_articles)} articles au total ---")