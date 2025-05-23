import json
from datetime import datetime, timedelta

import feedparser
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow import DAG

# === VARIABLES DE CONFIGURATION ===

# Paramètres fixés pour la collecte initiale (manuelle ou ponctuelle)
ARXIV_CATEGORY = Variable.get("ARXIV_CATEGORY").strip()
START_DATE = datetime.strptime("2024-01-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")  # Date de filtre fixe

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_TRAINQ")  # File Redis dédiée à l'entraînement

MAX_RESULTS = 100

# === INITIALISATION CLIENT REDIS ===

def get_redis_client():
    """Crée un client Redis configuré à partir des variables d’environnement."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


# === TÂCHE 1 : Requête et filtrage du flux ArXiv ===

def fetch_arxiv(**context):
    """
    Récupère jusqu’à 3000 publications ArXiv dans la catégorie spécifiée.
    Ne conserve que celles publiées après START_DATE.
    Envoie le résultat dans XCom.
    """
    base_url = "http://export.arxiv.org/api/query"
    query = f"{ARXIV_CATEGORY or 'all'}"
    url = f"{base_url}?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={MAX_RESULTS}"

    feed = feedparser.parse(url)
    publications = []

    for entry in feed.entries:
        iso_updated = datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%SZ")
        if iso_updated > START_DATE:
            publications.append({
                "id": entry.id,
                "title": entry.title,
                "summary": entry.summary.strip(),
                "authors": [author.name for author in entry.authors],
                "link": next(link.href for link in entry.links if link.type == "text/html"),
                "category": entry.arxiv_primary_category['term'],
                "published": entry.published,
                "updated": entry.updated
            })

    print(f"Found {len(publications)} articles")
    context['ti'].xcom_push(key='arxiv_results', value=publications)


# === TÂCHE 2 : Envoi des données vers Redis ===

def push_to_redis(**context):
    """
    Récupère les articles collectés via XCom.
    Les envoie dans Redis sous forme de JSON sérialisés.
    """
    publications = context['ti'].xcom_pull(key='arxiv_results', task_ids='fetch_arxiv_train')
    client = get_redis_client()

    if not publications:
        print("Nothing to push")
        return
    else:
        print(f"Pushing {len(publications)} articles")

    for pub in publications:
        client.rpush(REDIS_QUEUE, json.dumps(pub))


# === DEFINITION DU DAG AIRFLOW ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
        dag_id="arxiv_to_redis_train",
        default_args=default_args,
        schedule_interval=None,  # Ce DAG est déclenché manuellement
        catchup=False,
        tags=["arxiv", "redis", "training"],
) as dag:

    # Tâche de récupération ArXiv
    fetch_arxiv_train = PythonOperator(
        task_id="fetch_arxiv_train",
        python_callable=fetch_arxiv,
        provide_context=True
    )

    # Tâche d'envoi Redis
    push_to_redis_train = PythonOperator(
        task_id="push_to_redis_train",
        python_callable=push_to_redis,
        provide_context=True
    )

    # Dépendance entre les tâches
    fetch_arxiv_train >> push_to_redis_train
