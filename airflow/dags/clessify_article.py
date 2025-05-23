from datetime import datetime, timedelta

import pymongo
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator

from airflow import DAG

# === VARIABLES ===

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_CLASSQ")

MONGO_URI = Variable.get("MONGO_URI")
MONGO_DB = Variable.get("MONGO_DB")
MONGO_COLLECTION = Variable.get("MONGO_CLASSIFIY")

MLFLOW_TRACKING_URI = Variable.get("MLFLOW_TRACKING_URI")

# === CONNEXIONS AUX BASES DE DONNÉES ===

def get_redis_client():
    """Retourne une instance client Redis connectée à l’hôte configuré."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def get_mongo_collection():
    """Retourne un handle sur la collection MongoDB cible."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]



# === CLASSIFY ===


# === TASK: Classify Articles from Redis ===

def classify_articles_from_redis():
    # redis_client = get_redis_client()
    # mongo_collection = get_mongo_collection()
    #
    # while True:
    #     item = redis_client.lpop(REDIS_QUEUE_NAME)
    #     if not item:
    #         print("[INFO] Aucun élément à classifier.")
    #         break
    #
    #     article = json.loads(item)
    #     title = article.get("title", "")
    #     summary = article.get("summary", "")
    #
    #     print(f"[INFO] Classification de l'article : {article.get('id')}")
    #
    #     try:
    #         classification_result = classify_article(title, summary)
    #         log_with_mlflow(title, summary, classification_result)
    #         article["predicted_category"] = classification_result["label"]
    #         article["classification_confidence"] = classification_result["score"]
    #         mongo_collection.insert_one(article)
    #         print(f"[OK] Classification enregistrée avec succès.")
    #     except Exception as e:
    #         print(f"[ERREUR] Problème lors de la classification : {e}")
    #         redis_client.lpush(REDIS_QUEUE_NAME, item)
    pess


# === DAG DEFINITION ===

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
    classify_task = PythonOperator(
        task_id="classify_and_log_article",
        python_callable=classify_articles_from_redis,
    )

    classify_task
