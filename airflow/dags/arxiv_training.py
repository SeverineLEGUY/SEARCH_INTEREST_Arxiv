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

import pandas as pd


from evidently.test_suite import TestSuite
from evidently.test_preset import DataStabilityTestPreset

from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

from evidently.pipeline.column_mapping import ColumnMapping



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

        # Log du fichier de données
        mlflow.log_artifact(data_file)

        # Sauvegarde du LabelEncoder
        label_encoder_file = f"{MLFLOW_LOCAL}/label_encoder.pkl"
        joblib.dump(encoder, label_encoder_file)
        mlflow.log_artifact(label_encoder_file)

        # ====================================================================
        # === AJOUT CRITIQUE : Sauvegarder l'ID du run dans une Variable Airflow ===
        # ====================================================================
        
        # Récupérer l'ID du run MLflow actuellement actif
        current_run_id = mlflow.active_run().info.run_id
        
        # Mettre à jour la Variable Airflow qui sera lue par le DAG de monitoring
        Variable.set("LATEST_TRAINING_RUN_ID", current_run_id) 
        
        print(f"MLflow Run ID du dernier entraînement sauvegardé : {current_run_id}")

        # 1. Créer le DataFrame de Référence (Embeddings et Target)
        df_reference = pd.DataFrame(
            embedded_texts,
            columns=[f"feature_{i}" for i in range(embedded_texts.shape[1])]
            )
# Ajout de la colonne 'target' pour un monitoring complet du Target Drift
        df_reference['target'] = encoded_labels 

# Définir le mapping des colonnes (utile surtout si les noms sont personnalisés, mais laissons-le pour l'exemple)
        column_mapping = ColumnMapping(
            target='target', 
            numerical_features=[f"feature_{i}" for i in range(embedded_texts.shape[1])],
            categorical_features=[] # Tous vos features sont des composantes d'embedding, donc numériques
            )

# 2. Sauvegarder le jeu de données de référence (CSV) et le logguer dans MLflow
        # --- AJOUT : dossier de référence Evidently ---
        evidently_reference_dir = os.path.join(MLFLOW_LOCAL, "evidently_reference")
        os.makedirs(evidently_reference_dir, exist_ok=True)
        reference_data_file = os.path.join(evidently_reference_dir, "reference_data.csv")
        df_reference.to_csv(reference_data_file, index=False)

        # Log du dossier complet dans MLflow
        mlflow.log_artifacts(evidently_reference_dir, artifact_path="evidently_reference")
        print(f"Jeu de données de référence Evidently sauvegardé dans MLflow.")

        # 3. Générer la TestSuite (Data Stability)
        # On vérifie la stabilité des données d'entraînement elles-mêmes (Reference vs Reference)
        data_stability_test = TestSuite(tests=[DataStabilityTestPreset()])
        data_stability_test.run(
            current_data=df_reference, 
            reference_data=df_reference, 
            column_mapping=column_mapping
        )
# Sauvegarde du résultat du test (JSON et HTML)
        test_suite_html = f"{MLFLOW_LOCAL}/initial_stability_test.html"
        data_stability_test.save_html(test_suite_html)
        mlflow.log_artifact(test_suite_html, artifact_path="evidently_report")
        mlflow.log_metric("initial_data_stability_pass", int(data_stability_test.as_dict()['success']))
        print(f"Test Suite de stabilité initiale générée et logguée: {data_stability_test.as_dict()['summary']['success']}")

    # 4. Générer le Report (Data Drift)
    # Génération d'un rapport visuel initial (Reference vs Reference)
        data_drift_report = Report(metrics=[DataDriftPreset()])
        data_drift_report.run(
            current_data=df_reference, 
            reference_data=df_reference, 
            column_mapping=column_mapping   
        )
# Sauvegarde du rapport (HTML)
        report_file = f"{MLFLOW_LOCAL}/initial_drift_report.html"
        data_drift_report.save_html(report_file)
        mlflow.log_artifact(report_file, artifact_path="evidently_report")
        print(f"Rapport de dérive initial sauvegardé dans MLflow.")


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
        schedule_interval=None,  
        # Déclenchement manuel ou via trigger externe
        catchup=False,
        tags=["arxiv", "ml", "training"]
) as dag:
    train_model_from_redis = PythonOperator(
        task_id="train_model_from_redis",
        python_callable=train_model_from_redis
    )

    train_model_from_redis
