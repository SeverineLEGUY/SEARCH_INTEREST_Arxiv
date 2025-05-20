#!/bin/bash

# Attendre que Airflow soit initialisé
airflow db migrate

# === ARXIV FETCH DAG ===
airflow variables set ARXIV_CATEGORY "cs.AI"
airflow variables set ARXIV_START_DATE "2024-01-01T00:00:00Z"

# === REDIS CONFIGURATION ===
airflow variables set REDIS_HOST "localhost"
airflow variables set REDIS_PORT "6379"
airflow variables set REDIS_QUEUE_NAME "arxiv_publications"

# === MONGODB CONFIGURATION ===
airflow variables set MONGO_URI "mongodb://localhost:27017/"
airflow variables set MONGO_DB "arxiv"
airflow variables set MONGO_COLLECTION "summaries"

# === OPENAI API KEY ===
airflow variables set OPENAI_API_KEY "your_openai_api_key"  # <-- à remplacer !

echo "[OK] Variables Airflow initialisées."
