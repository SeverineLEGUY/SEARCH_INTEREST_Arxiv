import json
from datetime import datetime, timedelta

import pymongo
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from mistralai import Mistral

from airflow import DAG

# === VARIABLES DE CONFIGURATION ===

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_CLASSQ")

MONGO_URI = Variable.get("MONGO_URI")
MONGO_DB = Variable.get("MONGO_DB")
MONGO_COLLECTION = Variable.get("MONGO_SUMMARIZE")

MISTRAL_API_KEY = Variable.get("MISTRAL_API_KEY")

# Client Mistral instancié une fois pour tout le DAG
mistral_client = Mistral(api_key=MISTRAL_API_KEY)


# === CONNEXIONS AUX BASES DE DONNÉES ===

def get_redis_client():
    """Retourne une instance client Redis connectée à l’hôte configuré."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def get_mongo_collection():
    """Retourne un handle sur la collection MongoDB cible."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]


# === FONCTION LLM : Résumé et traduction ===

def summarize_and_translate(text):
    """
    Utilise Mistral pour générer un résumé vulgarisé en français à partir d’un résumé scientifique en anglais.
    """
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
            raise ValueError("Aucune réponse de MistralAI.")

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'appel à MistralAI: {e}")


# === TÂCHE : Résumer les articles depuis Redis et stocker dans MongoDB ===

def process_articles_from_redis():
    """
    Consomme les articles depuis Redis, génère un résumé FR avec MistralAI,
    et insère le résultat enrichi dans MongoDB. Évite les doublons.
    """
    redis_client = get_redis_client()
    mongo_collection = get_mongo_collection()

    while True:
        item = redis_client.lpop(REDIS_QUEUE)
        if not item:
            print("[INFO] File Redis vide. Fin du traitement.")
            break

        article = json.loads(item)
        article_id = article.get("id")
        summary_en = article.get("summary", "")

        print(f"[INFO] Traitement de l'article : {article_id}")

        # Vérifie si l'article est déjà présent dans MongoDB
        if mongo_collection.find_one({"id": article_id}):
            print(f"[INFO] Article {article_id} déjà présent dans MongoDB. Ignoré.")
            continue

        try:
            summary_fr = summarize_and_translate(summary_en)
        except Exception as e:
            print(f"[ERREUR] Échec du résumé/traduction : {e}")
            redis_client.lpush(REDIS_QUEUE, item)
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
            redis_client.lpush(REDIS_QUEUE, item)


# === DEFINITION DU DAG AIRFLOW ===

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
        schedule_interval="*/30 * * * *",  # Exécution toutes les 30 minutes
        catchup=False,
        tags=["arxiv", "llm", "redis", "mongo", "mistral"],
) as dag:
    # Tâche unique : traitement des articles depuis Redis
    summarize_task = PythonOperator(
        task_id="summarize_and_store_article",
        python_callable=process_articles_from_redis,
    )

    summarize_task
