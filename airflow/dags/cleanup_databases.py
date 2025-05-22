from datetime import timedelta

import pymongo
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator

from airflow import DAG

# === VARIABLES ===

REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUES = [Variable.get("REDIS_TRAINQ"), Variable.get("REDIS_CLASSQ")]

MONGO_URI = Variable.get("MONGO_URI")
MONGO_DB = Variable.get("MONGO_DB")
MONGO_COLLECTION = Variable.get("MONGO_SUMMARIZE")


# === DB CONNECTIONS ===

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def get_mongo_collection():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]


# === TASKS ===

def clear_redis_queues():
    client = get_redis_client()
    for q in REDIS_QUEUES:
        deleted_count = client.delete(q)
        print(f"[INFO] Redis: {q} supprimée ({deleted_count} clé(s) supprimée(s)).")


def clear_mongo_collections():
    collection = get_mongo_collection()
    result = collection.delete_many({})
    print(f"[INFO] MongoDB: {result.deleted_count} documents supprimés de la collection.")


# === DAG DEFINITION ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
        dag_id="cleanup_redis_and_mongo",
        default_args=default_args,
        schedule_interval=None,  # déclenché manuellement ou sur demande
        catchup=False,
        tags=["maintenance", "redis", "mongo", "cleanup"],
) as dag:
    clear_redis_queues = PythonOperator(
        task_id="clear_redis_queues",
        python_callable=clear_redis_queues,
    )

    clear_mongo_collections = PythonOperator(
        task_id="clear_mongo_collections",
        python_callable=clear_mongo_collections,
    )

    clear_redis_queues >> clear_mongo_collections
