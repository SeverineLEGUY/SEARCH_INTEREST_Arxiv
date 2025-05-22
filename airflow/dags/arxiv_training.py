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

from airflow import DAG

# === VARIABLES DE CONFIGURATION ===
REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_TRAINQ")

MODEL_NAME = "ll-MiniLM-L6-v2"
NUM_SAMPLES = 1000  # Nombre max d'échantillons à tirer de Redis pour l'entraînement

# === CONFIGURATION MLFLOW ===
MLFLOW_TRACKING_URI = "http://backend-run-mlflow:5050"  # URL du serveur MLflow
os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI

os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Évite les warnings de Hugging Face


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
            data.append({"text": text, "label": sample["category"]})

    if not data:
        print("Aucune donnée disponible pour l'entraînement.")
        return

    # --- Préparation des données ---
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    encoder = LabelEncoder()
    encoded_labels = encoder.fit_transform(labels)

    # Embedding avec SentenceTransformer
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embedded_texts = embedder.encode(texts)

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
    mlflow.set_experiment("arxiv_classification")
    with mlflow.start_run():
        # args = TrainingArguments(
        #     output_dir="/tmp/arxiv_model",
        #     evaluation_strategy="no",
        #     per_device_train_batch_size=8,
        #     num_train_epochs=2,
        #     logging_dir="/tmp/logs",
        # )

        mlflow.log_param("embedding_model", "all-MiniLM-L6-v2")
        mlflow.log_param("classifier", "LogisticRegression")
        mlflow.log_param("n_classes", len(encoder.classes_))

        # Log des métriques
        mlflow.log_metric("accuracy", accuracy)

        # Log du modèle + input example
        input_example = np.array([embedded_texts[0]])
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            input_example=input_example
        )

        # Log du fichier de données
        # mlflow.log_artifact(data)

        # Sauvegarde du LabelEncoder
        label_encoder_path = "label_encoder.pkl"
        joblib.dump(encoder, label_encoder_path)
        mlflow.log_artifact(label_encoder_path)

        # trainer = Trainer(
        #     model=model,
        #     args=args,
        #     train_dataset=tokenized_dataset,
        # )
        #
        # trainer.train()
        #
        # # Log du modèle et des métadonnées
        # mlflow.log_param("model", MODEL_NAME)
        # mlflow.log_param("num_classes", len(set(encoded_labels)))
        # mlflow.log_metric("train_samples", len(texts))
        #
        # mlflow.pytorch.log_model(model, artifact_path="model")


# === DEFINITION DU DAG AIRFLOW ===

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
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
