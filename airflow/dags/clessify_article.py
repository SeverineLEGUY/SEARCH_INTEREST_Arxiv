import json
from datetime import datetime, timedelta

import pymongo
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow import DAG
import mlflow
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer

# === VARIABLES DE CONFIGURATION ===

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_CLASSQ")

MONGO_URI = Variable.get("MONGO_URI")
MONGO_DB = Variable.get("MONGO_DB")
MONGO_COLLECTION = Variable.get("MONGO_CLASSIFY")

MLFLOW_TRACKING_URI = Variable.get("MLFLOW_TRACKING_URI")
MLFLOW_LOCAL = "/opt/airflow/mlflow"
MODEL_NAME = "all-MiniLM-L6-v2"


# === CONNEXIONS AUX BASES DE DONNÉES ===

def get_redis_client():
    """Retourne une instance client Redis connectée à l’hôte configuré."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def get_mongo_collection():
    """Retourne un handle sur la collection MongoDB cible."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]


# === TÂCHES ===

def classify_articles_from_redis():
    """
    Consomme des articles depuis Redis, applique une classification ML,
    et stocke le résultat enrichi dans MongoDB si l'article est nouveau.
    """
    redis_client = get_redis_client()
    mongo_collection = get_mongo_collection()

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    model_uri = "models:/arxiv_classification/Production"

    try:
        model = mlflow.sklearn.load_model(model_uri)
        encoder = joblib.load(f"{MLFLOW_LOCAL}/label_encoder.pkl")
    except Exception as e:
        print(f"[ERREUR] Chargement du modèle ou de l’encodeur impossible : {e}")
        return

    embedder = SentenceTransformer(MODEL_NAME)

    while True:
        item = redis_client.lpop(REDIS_QUEUE)
        if not item:
            print("[INFO] File Redis vide. Fin du traitement.")
            break

        article = json.loads(item)
        article_id = article.get("id")

        if mongo_collection.find_one({"id": article_id}):
            print(f"[INFO] Article {article_id} déjà présent dans MongoDB. Ignoré.")
            continue

        if "category" not in article:
            print(f"[INFO] Article sans catégorie. Ignoré.")
            continue

        text = article["title"] + " " + article["summary"]
        category = article["category"]
        main_category = category.split('.')[0]

        embedded_text = embedder.encode([text])
        predicted_class = model.predict(embedded_text)[0]
        label = encoder.inverse_transform([predicted_class])[0]
        article[label] = label  # Ajout de la classification au document

       # POUR EVIDENTLY  ===
        # Convertir l'array NumPy en liste Python pour MongoDB.
        # On stocke le vecteur embedded_text (nos features) sous la clé 'embedding'.
        article['embedding'] = embedded_text[0].tolist() 

        print(f"Texte classé comme : {label}. Catégorie réelle {main_category}.")

        try:
            mongo_collection.insert_one(article)
            print(f"[OK] Article inséré dans MongoDB avec classification.")
        except Exception as e:
            print(f"[ERREUR] Échec de l'insertion MongoDB : {e}")
            redis_client.lpush(REDIS_QUEUE, item)


# === DEFINITION DU DAG AIRFLOW ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
        dag_id="classify_arxiv_article",
        default_args=default_args,
        start_date=datetime(2025, 1, 1),
        schedule_interval="*/45 * * * *",  # Toutes les 45 minutes
        catchup=False,
        tags=["arxiv", "classification", "huggingface", "mlflow"],
) as dag:
    classify_articles_from_redis = PythonOperator(
        task_id="classify_articles_from_redis",
        python_callable=classify_articles_from_redis,
    )

    classify_articles_from_redis
