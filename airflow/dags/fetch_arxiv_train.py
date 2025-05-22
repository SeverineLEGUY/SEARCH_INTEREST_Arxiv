import json
from datetime import datetime, timedelta

import feedparser
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator

from airflow import DAG

# === VARIABLES ===

ARXIV_CATEGORY = Variable.get("ARXIV_CATEGORY").strip()
START_DATE = datetime.strptime("2024-01-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_TRAINQ")


# === DB CONNECTION ===

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


# === TASK: Fetch from ArXiv ===

def fetch_arxiv(**context):
    base_url = "http://export.arxiv.org/api/query"
    max_results = 1000
    query = f"cat:{ARXIV_CATEGORY or 'all:*'}"
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

    context['ti'].xcom_push(key='arxiv_results', value=publications)


# === TASK: Push to Redis ===

def push_to_redis(**context):
    publications = context['ti'].xcom_pull(key='arxiv_results', task_ids='fetch_arxiv')
    client = get_redis_client()

    if not publications:
        return

    for pub in publications:
        client.rpush(REDIS_QUEUE, json.dumps(pub))


# === DAG DEFINITION ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
        dag_id="arxiv_to_redis_train",
        default_args=default_args,
        schedule_interval=None,  # déclenché manuellement ou sur demande
        catchup=False,
        tags=["arxiv", "redis", "training"],
) as dag:
    fetch_arxiv_train = PythonOperator(
        task_id="fetch_arxiv_train",
        python_callable=fetch_arxiv,
        provide_context=True
    )

    push_to_redis_train = PythonOperator(
        task_id="push_to_redis_train",
        python_callable=push_to_redis,
        provide_context=True
    )

    fetch_arxiv_train >> push_to_redis_train
