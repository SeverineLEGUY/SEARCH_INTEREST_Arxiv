#!/bin/bash

# Attendre que Airflow soit initialisé
airflow db migrate

# === ARXIV FETCH DAG ===
airflow variables set ARXIV_CATEGORY "cs.AI"
airflow variables set ARXIV_START_DATE "2024-01-01T00:00:00Z"

# === REDIS CONFIGURATION ===
airflow variables set REDIS_HOST "airflow-run-redis"
airflow variables set REDIS_PORT "6379"
airflow variables set REDIS_QUEUE_NAME "arxiv_publications"

# === MONGODB CONFIGURATION ===
airflow variables set MONGO_URI "mongodb://backend-run-mongodb:27017/"
airflow variables set MONGO_DB "arxiv"
airflow variables set MONGO_COLLECTION "summaries"

# === MISTRALAI API KEY ===
airflow variables set MISTRAL_API_KEY "9nDAmd7DksYDiwFeLQIkSq7pktOcZkgk"  # EXPIRES 2025-05-31

echo "[OK] Variables Airflow initialisées."
