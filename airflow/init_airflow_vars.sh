#!/bin/bash

# Charger les variables d'environnement depuis un fichier .env si présent
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# === Déclaration des variables Airflow ===

# ARXIV
ARXIV_CATEGORY=""
ARXIV_START_DATE="2025-01-01T00:00:00Z"

# REDIS
REDIS_HOST="airflow-run-redis"
REDIS_PORT="6379"
REDIS_QUEUE_NAME="arxiv_publications"

# MONGODB
MONGO_URI="mongodb://backend-run-mongodb:27017/"
MONGO_DB="arxiv"
MONGO_SUMMARIZE="arxiv_summaries"
MONGO_CLASSIFIY="arxiv_classifications"

# MLFLOW
MLFLOW_TRACKING_URI="http://backend-run-mlflow:5050"

# HUGGINGFACE
HUGGINGFACE_USERNAME="<username>" # Remplacez par votre nom d'utilisateur Hugging Face
HUGGINGFACE_MODELNAME="arxiv-classifier-dsl-31-final-project"
HUGGINGFACE_API_URL="https://api-inference.huggingface.co/models/$HUGGINGFACE_USERNAME/$HUGGINGFACE_MODELNAME"
HUGGINGFACE_TOKEN=""

# MISTRALAI
MISTRAL_API_KEY="9nDAmd7DksYDiwFeLQIkSq7pktOcZkgk" # EXPIRES 2025-05-31

# === Initialisation Airflow ===

# Attendre que la base de données Airflow soit prête
airflow db migrate

# === Configuration des variables dans Airflow ===

# ARXIV
airflow variables set ARXIV_CATEGORY "$ARXIV_CATEGORY"
airflow variables set ARXIV_START_DATE "$ARXIV_START_DATE"

# REDIS
airflow variables set REDIS_HOST "$REDIS_HOST"
airflow variables set REDIS_PORT "$REDIS_PORT"
airflow variables set REDIS_QUEUE_NAME "$REDIS_QUEUE_NAME"

# MONGODB
airflow variables set MONGO_URI "$MONGO_URI"
airflow variables set MONGO_DB "$MONGO_DB"
airflow variables set MONGO_SUMMARIZE "$MONGO_SUMMARIZE"
airflow variables set MONGO_CLASSIFIY "$MONGO_CLASSIFIY"

# MLFLOW
airflow variables set MLFLOW_TRACKING_URI "$MLFLOW_TRACKING_URI"

# HUGGINGFACE
airflow variables set HUGGINGFACE_USERNAME "$HUGGINGFACE_USERNAME"
airflow variables set HUGGINGFACE_MODELNAME "$HUGGINGFACE_MODELNAME"
airflow variables set HUGGINGFACE_API_URL "$HUGGINGFACE_API_URL"
airflow variables set HUGGINGFACE_TOKEN "$HUGGINGFACE_TOKEN"

# MISTRALAI
airflow variables set MISTRAL_API_KEY "$MISTRAL_API_KEY"

echo "[OK] Variables Airflow initialisées."
