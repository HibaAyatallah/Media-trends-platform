import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any

from kafka import KafkaProducer

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constantes de configuration pour Kafka
# Permet de définir le broker via une variable d'environnement (ex: pour Docker)
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = "news_articles"

def get_kafka_producer() -> KafkaProducer:
    """
    Initialise et retourne une instance de KafkaProducer.
    Configure automatiquement la sérialisation en JSON.
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            # Fonction anonyme pour convertir le dict Python en JSON encodé en UTF-8
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5  # Réessaie 5 fois en cas d'échec de connexion
        )
        logging.info(f"Connexion réussie au broker Kafka sur {KAFKA_BOOTSTRAP_SERVERS}")
        return producer
    except Exception as e:
        logging.error(f"Erreur de connexion à Kafka ({KAFKA_BOOTSTRAP_SERVERS}) : {e}")
        return None


def send_article_to_kafka(article: Dict[str, Any], producer: KafkaProducer = None):
    """
    Envoie un événement (un article) vers le topic Kafka configuré.
    Le format attendu correspond au modèle défini (title, author, content, etc.).
    """
    if producer is None:
        producer = get_kafka_producer()
        
    if not producer:
        logging.warning(f"Impossible d'envoyer l'article '{article.get('title')}', producteur indisponible.")
        return

    # S'assurer que l'heure de collecte (scraped_at) est toujours présente
    if "scraped_at" not in article:
        article["scraped_at"] = datetime.now(timezone.utc).isoformat()

    try:
        # Envoi asynchrone du message
        future = producer.send(KAFKA_TOPIC, value=article)
        
        # Le .get() force une attente synchrone pour garantir que le message est bien parti
        # (Utile principalement pour le logging)
        record_metadata = future.get(timeout=10)
        logging.info(
            f"Article '{article.get('title')}' envoyé avec succès "
            f"[Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}]"
        )
    except Exception as e:
        logging.error(f"Échec de l'envoi de l'article vers Kafka : {e}")


def simulate_streaming():
    """
    Fonction de test qui génère et envoie des données fictives
    pour simuler un flux d'ingestion en temps réel.
    """
    logging.info("--- Démarrage de la simulation de streaming Kafka ---")
    
    producer = get_kafka_producer()
    if not producer:
        logging.error("Simulation interrompue : Kafka injoignable.")
        return
        
    # Liste de 3 articles fictifs respectant le schéma demandé
    dummy_articles = [
        {
            "title": "Nouveau record historique pour le marché boursier européen",
            "author": "Alice Dupuis",
            "publication_date": "2026-05-14T10:00:00",
            "category": "Économie",
            "content": "Le marché mondial a atteint un nouveau sommet aujourd'hui, propulsé par les valeurs technologiques et l'intelligence artificielle.",
            "source": "Finance Echo",
            "url": "http://finance-echo.com/record-bourse-europe"
        },
        {
            "title": "Avancée majeure dans la recherche sur la fusion nucléaire",
            "author": "Dr. Jean Dupont",
            "publication_date": "2026-05-14T10:05:00",
            "category": "Science",
            "content": "Des chercheurs ont réussi à maintenir une réaction de fusion stable pendant plus de 30 secondes, un record absolu pour le réacteur expérimental.",
            "source": "Science Daily",
            "url": "http://sciencedaily.com/fusion-breakthrough"
        },
        {
            "title": "Résultats inattendus du tournoi de tennis majeur",
            "author": "Marc Sportif",
            "publication_date": "2026-05-14T10:15:00",
            "category": "Sport",
            "content": "Le favori absolu a été éliminé dès le premier tour dans un match époustouflant en cinq sets face au 150ème joueur mondial.",
            "source": "Sport Hebdo",
            "url": "http://sporthebdo.fr/tennis-surprise-tournoi"
        }
    ]

    for idx, article in enumerate(dummy_articles, start=1):
        logging.info(f"Génération de l'article {idx}/{len(dummy_articles)}...")
        send_article_to_kafka(article, producer)
        
        # Pause artificielle pour simuler le délai entre les vrais articles
        if idx < len(dummy_articles):
            time.sleep(2)
        
    # Vider le buffer pour s'assurer que tous les messages partent avant de couper le script
    producer.flush()
    logging.info("--- Fin de la simulation de streaming Kafka ---")

if __name__ == "__main__":
    simulate_streaming()
