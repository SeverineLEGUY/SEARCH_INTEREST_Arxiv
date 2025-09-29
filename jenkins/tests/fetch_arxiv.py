import json
from datetime import datetime, timedelta

import feedparser
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow import DAG

# === VARIABLES DE CONFIGURATION ===

# Récupération des variables Airflow (via l'interface ou la CLI)
ARXIV_CATEGORY = Variable.get("ARXIV_CATEGORY").strip()
START_DATE = Variable.get("ARXIV_START_DATE", default_var="2025-01-01T00:00:00Z")
START_DATE = datetime.strptime(START_DATE, "%Y-%m-%dT%H:%M:%SZ")  # Format ISO 8601 (UTC)

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_CLASSQ")


# === INITIALISATION CLIENT REDIS ===

def get_redis_client():
    """Instancie un client Redis connecté au host/port définis en variables."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


# === TÂCHE 1 : Requête et filtrage du flux ArXiv ===

def fetch_arxiv(**context):
    """
    Récupère les dernières publications ArXiv dans la catégorie spécifiée.
    Filtre les résultats en fonction de START_DATE.
    Les résultats sont poussés dans XCom pour la tâche suivante.
    """
    base_url = "http://export.arxiv.org/api/query"
    max_results = 100
    query = f"{ARXIV_CATEGORY or 'all'}"
    url = f"{base_url}?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

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


# === TÂCHE 2 : Envoi des publications dans Redis ===

def push_to_redis(**context):
    """
    Récupère les publications depuis XCom.
    Les sérialise en JSON et les pousse dans la file Redis.
    Met à jour la variable START_DATE avec le dernier timestamp traité.
    """
    publications = context['ti'].xcom_pull(key='arxiv_results', task_ids='fetch_arxiv')
    client = get_redis_client()

    if not publications:
        print("Nothing to push")
        return
    else:
        print(f"Pushing {len(publications)} articles")

    for pub in publications:
        client.rpush(REDIS_QUEUE, json.dumps(pub))

    # Mémorisation du dernier article pour le prochain run
    newest_update = publications[0]['updated']
    Variable.set("ARXIV_START_DATE", newest_update)


# === DEFINITION DU DAG AIRFLOW ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
        dag_id="arxiv_to_redis",
        default_args=default_args,
        start_date=datetime(2025, 1, 1),
        schedule_interval="*/8 * * * *",  # Exécution toutes les 8 minutes
        catchup=False,
        tags=["arxiv", "redis"],
) as dag:
    # Tâche 1 : Lecture du flux ArXiv
    fetch_arxiv = PythonOperator(
        task_id="fetch_arxiv",
        python_callable=fetch_arxiv,
        provide_context=True
    )

    # Tâche 2 : Envoi vers Redis
    push_to_redis = PythonOperator(
        task_id="push_to_redis",
        python_callable=push_to_redis,
        provide_context=True
    )

    # Ordonnancement des tâches
    fetch_arxiv >> push_to_redis
