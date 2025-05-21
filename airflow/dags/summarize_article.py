import json
from datetime import datetime, timedelta

import pymongo
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from mistralai import Mistral

from airflow import DAG

# === VARIABLES ===

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE_NAME = Variable.get("REDIS_QUEUE_NAME")

MONGO_URI = Variable.get("MONGO_URI")
MONGO_DB = Variable.get("MONGO_DB")
MONGO_COLLECTION = Variable.get("MONGO_SUMMARIZE")

MISTRAL_API_KEY = Variable.get("MISTRAL_API_KEY")

mistral_client = Mistral(api_key=MISTRAL_API_KEY)


# === DB CONNECTIONS ===

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def get_mongo_collection():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]


# === SUMMARIZE AND TRANSLATE ===

def summarize_and_translate(text):
    prompt = f"""
Analyse le texte scientifique entre les balises #BEGIN_TEXT# et #END_TEXT# puis résume-le pour un public non spécialiste.
Le résultat attendu doit être un texte en français, sans balises ni annotations supplémentaires.
#BEGIN_TEXT#
{text}
#END_TEXT#
"""
    try:
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200,
        )

        if not response.choices:
            raise ValueError("Aucune réponse de Mistral.")

        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'appel à Mistral: {e}")


# === TASK: Summarize Articles from Redis ===

def process_articles_from_redis():
    redis_client = get_redis_client()
    mongo_collection = get_mongo_collection()

    while True:
        item = redis_client.lpop(REDIS_QUEUE_NAME)
        if not item:
            print("[INFO] File Redis vide. Fin du traitement.")
            break

        article = json.loads(item)
        summary_en = article.get("summary", "")

        print(f"[INFO] Traitement de l'article : {article.get('id')}")

        try:
            summary_fr = summarize_and_translate(summary_en)
        except Exception as e:
            print(f"[ERREUR] Échec du résumé/traduction : {e}")
            # On remet l'article dans la file pour le retenter plus tard
            redis_client.lpush(REDIS_QUEUE_NAME, item)
            continue

        article["summary_fr"] = summary_fr

        print("[Résumé anglais]")
        print(summary_en)
        print("[Résumé français]")
        print(summary_fr)

        try:
            mongo_collection.insert_one(article)
            print(f"[OK] Article inséré dans MongoDB avec résumé français.")
        except Exception as e:
            print(f"[ERREUR] Échec de l'insertion MongoDB : {e}")
            redis_client.lpush(REDIS_QUEUE_NAME, item)


# === DAG DEFINITION ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
        dag_id="summarize_arxiv_article",
        default_args=default_args,
        start_date=datetime(2025, 1, 1),
        schedule_interval="*/30 * * * *",  # Toutes les 30 minutes
        catchup=False,
        tags=["arxiv", "llm", "redis", "mongo", "mistral"],
) as dag:
    summarize_task = PythonOperator(
        task_id="summarize_and_store_article",
        python_callable=process_articles_from_redis,
    )

    summarize_task
