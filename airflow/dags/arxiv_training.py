import json
import os
from datetime import timedelta

import joblib
import mlflow
import mlflow.sklearn
import mlflow.sklearn
import numpy as np
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import csv
import uuid

from airflow import DAG

# === VARIABLES DE CONFIGURATION ===
REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_TRAINQ")

MLFLOW_TRACKING_URI = Variable.get("MLFLOW_TRACKING_URI")
MLFLOW_LOCAL = "/opt/airflow/mlflow"

# === CONFIGURATION MLFLOW ===
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Évite les warnings de Hugging Face

MODEL_NAME = "all-MiniLM-L6-v2"


# === CONNEXION AUX BASES DE DONNÉES ===

def get_redis_client():
    """Retourne une instance client Redis connectée à l’hôte configuré."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


# === TÂCHES ===

def train_model_from_redis():
    """Extrait les données de Redis, entraîne un modèle SciBERT et logue l'expérience via MLflow."""
    redis_client = get_redis_client()
    data = []

    while True:
        item = redis_client.lpop(REDIS_QUEUE)
        if not item:
            break
        sample = json.loads(item)
        if "category" in sample:
            text = sample["title"] + " " + sample["summary"]
            category = sample["category"]
            main_category = category.split('.')[0]
            data.append({"text": text, "label": main_category})

    if not data:
        print("Aucune donnée disponible pour l'entraînement.")
        return
    else:
        print(f"Entraînement sur {len(data)} samples.")

    unique_id = uuid.uuid4()
    data_file = f"{MLFLOW_LOCAL}/data_{unique_id}.csv"

    # Champs à écrire dans le CSV
    fieldnames = ["text", "label"]

    # Écriture des données dans le fichier
    with open(data_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"Données écrites dans {data_file}")

    # --- Préparation des données ---
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    encoder = LabelEncoder()
    encoded_labels = encoder.fit_transform(labels)

    # Embedding avec SentenceTransformer
    embedder = SentenceTransformer(MODEL_NAME)
    embedded_texts = embedder.encode(texts, show_progress_bar=True)

    # Entraînement du modèle
    model = LogisticRegression(max_iter=1000)
    model.fit(embedded_texts, encoded_labels)

    # Prédictions
    predicted_labels = model.predict(embedded_texts)

    report = classification_report(encoded_labels, predicted_labels, target_names=encoder.classes_)
    accuracy = accuracy_score(encoded_labels, predicted_labels)

    print("Classification Report:\n", report)
    print(f"Accuracy: {accuracy}")

    # --- Suivi avec MLflow ---
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("arxiv_classification")
    with mlflow.start_run():
        mlflow.log_param("embedding_model", MODEL_NAME)
        mlflow.log_param("classifier", "LogisticRegression")
        mlflow.log_param("num_classes", len(encoder.classes_))
        mlflow.log_metric("train_samples", len(texts))

        # Log des métriques
        mlflow.log_metric("accuracy", accuracy)

        # Log du modèle + input example
        input_example = np.array([embedded_texts[0]])
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            input_example=input_example
        )
        print("C")

        # Log du fichier de données
        print("D")
        mlflow.log_artifact(data_file)
        print("E")

        # Sauvegarde du LabelEncoder
        print("F")
        label_encoder_file = f"{MLFLOW_LOCAL}/label_encoder.pkl"
        print("G")
        joblib.dump(encoder, label_encoder_file)
        print("H")
        mlflow.log_artifact(label_encoder_file)
        print("I")


# === DEFINITION DU DAG AIRFLOW ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
        dag_id="arxiv_training",
        default_args=default_args,
        schedule_interval=None,  # Déclenchement manuel ou via trigger externe
        catchup=False,
        tags=["arxiv", "ml", "training"]
) as dag:
    train_model_from_redis = PythonOperator(
        task_id="train_model_from_redis",
        python_callable=train_model_from_redis
    )

    train_model_from_redis
