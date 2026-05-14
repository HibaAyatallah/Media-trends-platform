-- Schéma SQL pour le Data Warehouse PostgreSQL de Media Trends Platform

-- --------------------------------------------------------
-- TABLES DE DIMENSION
-- --------------------------------------------------------

-- Table dim_source : Liste des sources d'actualités (ex: Hespress, BBC)
CREATE TABLE IF NOT EXISTS dim_source (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) UNIQUE NOT NULL
);

-- Table dim_category : Liste des catégories d'articles
CREATE TABLE IF NOT EXISTS dim_category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) UNIQUE NOT NULL
);

-- --------------------------------------------------------
-- TABLE DE FAITS
-- --------------------------------------------------------

-- Table fact_articles : Informations principales sur les articles
CREATE TABLE IF NOT EXISTS fact_articles (
    article_id SERIAL PRIMARY KEY,
    title TEXT,
    publication_date DATE,
    source_id INT,
    category_id INT,
    url TEXT UNIQUE,
    content_length INT,
    
    -- Clés étrangères vers les tables de dimension
    CONSTRAINT fk_source
        FOREIGN KEY (source_id) 
        REFERENCES dim_source(source_id)
        ON DELETE SET NULL,
        
    CONSTRAINT fk_category
        FOREIGN KEY (category_id) 
        REFERENCES dim_category(category_id)
        ON DELETE SET NULL
);

-- --------------------------------------------------------
-- TABLES D'AGRÉGATION (GOLD LAYER)
-- --------------------------------------------------------

-- Table agg_articles_by_day : Volumétrie des articles par jour
CREATE TABLE IF NOT EXISTS agg_articles_by_day (
    publication_date DATE PRIMARY KEY,
    number_of_articles INT NOT NULL DEFAULT 0
);

-- Table agg_articles_by_source : Volumétrie des articles par source
CREATE TABLE IF NOT EXISTS agg_articles_by_source (
    source_name VARCHAR(255) PRIMARY KEY,
    number_of_articles INT NOT NULL DEFAULT 0
);

-- Table agg_top_keywords : Fréquence d'apparition des mots-clés
CREATE TABLE IF NOT EXISTS agg_top_keywords (
    keyword VARCHAR(255) PRIMARY KEY,
    frequency INT NOT NULL DEFAULT 0
);
