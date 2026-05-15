import os
import json
import logging
from datetime import datetime
from kafka import KafkaConsumer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "news_articles"

def save_to_bronze(article: dict):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    bronze_dir = os.path.join(project_root, "data_lake", "bronze")
    os.makedirs(bronze_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"stream_bronze_{timestamp}.json"
    filepath = os.path.join(bronze_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([article], f, ensure_ascii=False, indent=4)
    logging.info(f"Article sauvegardé en Bronze : {filename}")

def run_consumer():
    logging.info("--- Démarrage du Consumer Kafka ---")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='media-trends-group',
        consumer_timeout_ms=10000
    )
    count = 0
    for message in consumer:
        article = message.value
        logging.info(f"Article reçu : {article.get('title')} [Offset: {message.offset}]")
        save_to_bronze(article)
        count += 1
    consumer.close()
    logging.info(f"--- Consumer terminé : {count} articles traités ---")

if __name__ == "__main__":
    run_consumer()
