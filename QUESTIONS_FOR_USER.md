# Questions pour l'Utilisateur (Finalisation du Projet)

Pour s'assurer que ce projet correspond parfaitement à vos attentes académiques et à la soutenance prévue, j'ai besoin de clarifier quelques points :

## Questions Stratégiques et Métier
1. **Périmètre du Scraping** : Actuellement, le scraper cible Hespress et BBC de manière très basique. Quels sont les sites d'actualité précis que vous souhaitez analyser dans le cadre de votre soutenance ?
2. **Utilisation du Data Lake (MinIO)** : Nous avons configuré l'architecture Medallion avec des dossiers locaux (`data_lake/bronze`...) mais inclus MinIO dans Docker. Est-il impératif académiquement de stocker la donnée Bronze/Silver dans des buckets MinIO/S3 via la librairie `boto3`, ou l'approche "fichiers locaux" suffit-elle ?
3. **Objectif du Streaming (Kafka)** : Actuellement, le producteur Kafka génère des données fictives. Est-ce que le streaming (Kafka) doit être purement démonstratif pour le projet, ou doit-on développer un consommateur Kafka réel pour intégrer ces données dans le Data Lake ?

## Questions Organisationnelles
4. **Cadre Académique** : Est-ce que le projet est individuel ou en binôme ? Quel nom dois-je mettre dans le `README.md` (Nom, Prénom, École/Filière) ?
5. **Livraison** : Quelle est la date de rendu final ?
6. **Docker** : Est-ce que le projet doit impérativement être évalué en exécutant Docker, ou devez-vous également fournir une version pouvant s'exécuter de façon très "simple" (100% locale sans conteneurisation) pour les examinateurs ?
7. **Restitution** : Veux-tu utiliser Streamlit comme nous l'avons fait, ou l'utilisation d'un outil BI standard (comme Metabase ou Superset) connecté à PostgreSQL est-elle attendue par vos professeurs ?
8. **Soutenance** : Auriez-vous besoin de support pour construire la présentation PowerPoint (schémas d'architecture) à l'issue de ce projet technique ?
