import json
import os
from datetime import timedelta

import mlflow
import redis
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from datasets import Dataset
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

from airflow import DAG

# === CONFIGURATION ===
REDIS_HOST = Variable.get("REDIS_HOST")
REDIS_PORT = int(Variable.get("REDIS_PORT"))
REDIS_QUEUE = Variable.get("REDIS_TRAINQ")

MODEL_NAME = "allenai/scibert_scivocab_uncased"
NUM_SAMPLES = 1000  # Nombre max d'échantillons à tirer de Redis pour l'entraînement

# === CONFIGURATION MLflow ===
MLFLOW_TRACKING_URI = "http://backend-run-mlflow:5050"  # Remplacer avec l'URL de ton serveur MLflow
os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI  # Définir la variable d'environnement MLflow


# === DB CONNECTIONS ===

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def train_model_from_redis():
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

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_function(example):
        return tokenizer(example["text"], padding="max_length", truncation=True)

    dataset = Dataset.from_dict({"text": texts, "label": encoded_labels})
    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=len(set(encoded_labels)))

    # --- MLflow Tracking ---
    mlflow.set_experiment("arxiv_classification")
    with mlflow.start_run():
        args = TrainingArguments(
            output_dir="/tmp/arxiv_model",
            evaluation_strategy="no",
            per_device_train_batch_size=8,
            num_train_epochs=2,
            logging_dir="/tmp/logs",
        )

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=tokenized_dataset,
        )

        trainer.train()

        # Log du modèle et des métadonnées
        mlflow.log_param("model", MODEL_NAME)
        mlflow.log_param("num_classes", len(set(encoded_labels)))
        mlflow.log_metric("train_samples", len(texts))

        mlflow.pytorch.log_model(model, artifact_path="model")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
        dag_id="arxiv_training",
        default_args=default_args,
        schedule_interval=None,  # déclenché manuellement ou sur demande
        catchup=False,
        tags=["arxiv", "ml", "training"]
) as dag:
    train_model_from_redis = PythonOperator(
        task_id="train_model_from_redis",
        python_callable=train_model_from_redis
    )

    train_model_from_redis
