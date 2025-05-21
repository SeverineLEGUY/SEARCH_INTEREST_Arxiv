import json
from datetime import datetime, timedelta

import feedparser
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator

from airflow import DAG

# === VARIABLES ===

ARXIV_CATEGORY = Variable.get("ARXIV_CATEGORY")
START_DATE = Variable.get("ARXIV_START_DATE")

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE_NAME = Variable.get("REDIS_QUEUE_NAME")


# === DB CONNECTION ===

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


# === TASK: Fetch from ArXiv ===

def fetch_arxiv_publications(**context):
    base_url = "http://export.arxiv.org/api/query"
    max_results = 10
    query = f"cat:{ARXIV_CATEGORY}"
    url = f"{base_url}?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

    feed = feedparser.parse(url)
    publications = []

    for entry in feed.entries:
        published = entry.published
        if published >= START_DATE:
            publications.append({
                "id": entry.id,
                "title": entry.title,
                "authors": [author.name for author in entry.authors],
                "summary": entry.summary,
                "published": published,
                "link": entry.link
            })

    context['ti'].xcom_push(key='arxiv_results', value=publications)


# === TASK: Push to Redis ===

def push_to_redis(**context):
    publications = context['ti'].xcom_pull(key='arxiv_results', task_ids='fetch_arxiv')
    client = get_redis_client()

    for pub in publications:
        client.rpush(REDIS_QUEUE_NAME, json.dumps(pub))


# === DAG DEFINITION ===

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
        schedule_interval="*/8 * * * *",  # Toutes les 8 minutes
        catchup=False,
        tags=["arxiv", "redis"],
) as dag:
    fetch_arxiv = PythonOperator(
        task_id="fetch_arxiv",
        python_callable=fetch_arxiv_publications,
        provide_context=True
    )

    push_redis = PythonOperator(
        task_id="push_to_redis",
        python_callable=push_to_redis,
        provide_context=True
    )

    fetch_arxiv >> push_redis
