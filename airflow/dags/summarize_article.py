from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import redis
import json
import pymongo

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# === VARIABLES AIRFLOW ===

REDIS_HOST = Variable.get("REDIS_HOST", default_var="localhost")
REDIS_PORT = int(Variable.get("REDIS_PORT", default_var="6379"))
REDIS_QUEUE_NAME = Variable.get("REDIS_QUEUE_NAME", default_var="arxiv_publications")

MONGO_URI = Variable.get("MONGO_URI", default_var="mongodb://localhost:27017/")
MONGO_DB = Variable.get("MONGO_DB", default_var="arxiv")
MONGO_COLLECTION = Variable.get("MONGO_COLLECTION", default_var="summaries")

MISTRAL_API_KEY = Variable.get("MISTRAL_API_KEY", default_var="your_mistral_api_key")
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

# === REDIS ===

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# === MONGO ===

def get_mongo_collection():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]

# === LLM: Résumé + Traduction ===

def summarize_and_translate(text):
    prompt = f"""
Lis le texte suivant, résume-le en un seul paragraphe et traduis ce résumé en français. Voici le texte :

{text}
"""
    try:
        response = mistral_client.chat(
            model="mistral-large-latest",  # ou mistral-small-latest selon ton plan
            messages=[ChatMessage(role="user", content=prompt)],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'appel à Mistral: {e}")

# === TÂCHE PRINCIPALE ===

def process_article_from_redis():
    redis_client = get_redis_client()
    mongo_collection = get_mongo_collection()

    item = redis_client.lpop(REDIS_QUEUE_NAME)
    if not item:
        print("[INFO] Aucun élément à traiter dans Redis.")
        return

    article = json.loads(item)
    summary_en = article.get("summary", "")

    print(f"[INFO] Traitement de l'article : {article.get('id')}")

    try:
        summary_fr = summarize_and_translate(summary_en)
    except Exception as e:
        print(f"[ERREUR] Échec du résumé/traduction : {e}")
        return

    article["summary_fr"] = summary_fr

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
    dag_id="summarize_arxiv_article_with_mistral",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="*/5 * * * *",  # Toutes les 5 minutes
    catchup=False,
    tags=["arxiv", "llm", "redis", "mongo", "mistral"],
) as dag:

    summarize_task = PythonOperator(
        task_id="summarize_and_store_article",
        python_callable=process_article_from_redis,
    )

    summarize_task
