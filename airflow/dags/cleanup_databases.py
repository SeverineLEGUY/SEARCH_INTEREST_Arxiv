from datetime import timedelta

import pymongo
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow import DAG

# === VARIABLES DE CONFIGURATION ===

# Cibles Redis : files à nettoyer
REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUES = [Variable.get("REDIS_TRAINQ"), Variable.get("REDIS_CLASSQ")]

# Cible MongoDB : collection à vider
MONGO_URI = Variable.get("MONGO_URI")
MONGO_DB = Variable.get("MONGO_DB")
MONGO_COLLECTION = Variable.get("MONGO_SUMMARIZE")


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

def clear_redis_queues():
    """
    Supprime les files Redis spécifiées.
    Affiche le nombre de clés supprimées pour chaque file.
    """
    client = get_redis_client()
    for q in REDIS_QUEUES:
        deleted_count = client.delete(q)
        print(f"[INFO] Redis: {q} supprimée ({deleted_count} clé(s) supprimée(s)).")


def clear_mongo_collections():
    """
    Vide entièrement la collection MongoDB cible.
    Affiche le nombre de documents supprimés.
    """
    collection = get_mongo_collection()
    result = collection.delete_many({})
    print(f"[INFO] MongoDB: {result.deleted_count} documents supprimés de la collection.")


# === DEFINITION DU DAG AIRFLOW ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
        dag_id="cleanup_redis_and_mongo",
        default_args=default_args,
        schedule_interval=None,  # Exécution manuelle uniquement
        catchup=False,
        tags=["maintenance", "redis", "mongo", "cleanup"],
) as dag:

    # Tâche de purge des files Redis
    clear_redis_queues = PythonOperator(
        task_id="clear_redis_queues",
        python_callable=clear_redis_queues,
    )

    # Tâche de purge de la collection MongoDB
    clear_mongo_collections = PythonOperator(
        task_id="clear_mongo_collections",
        python_callable=clear_mongo_collections,
    )

    # Ordre d’exécution : Redis -> Mongo
    clear_redis_queues >> clear_mongo_collections
