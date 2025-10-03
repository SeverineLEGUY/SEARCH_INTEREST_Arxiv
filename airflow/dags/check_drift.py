from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import mlflow
import joblib
import pymongo
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow import DAG
from evidently.test_suite import TestSuite
from evidently.test_preset import DataStabilityTestPreset

from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

from evidently.pipeline.column_mapping import ColumnMapping
#from evidently.cli.client import EvidentlyClient # Si vous utilisez Evidently Cloud (voir 03-Real_time_monitoring.ipynb)

# === CONFIGURATION (Doit correspondre aux variables Airflow) ===
MONGO_URI = Variable.get("MONGO_URI")
MONGO_DB = Variable.get("MONGO_DB")
MONGO_COLLECTION = Variable.get("MONGO_CLASSIFY")
MLFLOW_TRACKING_URI = Variable.get("MLFLOW_TRACKING_URI")
MLFLOW_LOCAL = "/opt/airflow/mlflow" # Dossier de travail local

# NOTE: Vous devez définir les variables suivantes dans Airflow
#MLFLOW_RUN_ID = Variable.get("LATEST_TRAINING_RUN_ID") # ID du dernier run de arxiv_training
# Si utilisation de la version Cloud (Optionnel)
# EVIDENTLY_CLOUD_API_KEY = Variable.get("EVIDENTLY_CLOUD_API_KEY", default_var="")
# EVIDENTLY_PROJECT_ID = Variable.get("EVIDENTLY_PROJECT_ID", default_var="")




def run_drift_check(**context):
    
            # LECTURE DE LA VARIABLE AIRFLOW À L'INTÉRIEUR DE LA TÂCHE
    current_mlflow_run_id = Variable.get("LATEST_TRAINING_RUN_ID")
    # 1. Configuration MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


    
    # 2. Téléchargement des données de référence (doit contenir 'embedding' + 'target')
    # Ceci télécharge le dossier 'evidently_reference' (qui contient reference_data.csv)
    reference_artifact_path = mlflow.artifacts.download_artifacts(
        run_id=current_mlflow_run_id,
        artifact_path="evidently_reference", 
        dst_path=MLFLOW_LOCAL
    )
    df_reference = pd.read_csv(f"{reference_artifact_path}/reference_data.csv")
    
    # 3. Récupération des données de production (1 jour de données)
    client = pymongo.MongoClient(MONGO_URI)
    mongo_collection = client[MONGO_DB][MONGO_COLLECTION]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Récupérer les articles insérés avec la clé 'embedding' et 'label' dans la dernière période
    articles_prod = list(mongo_collection.find(
        {
            "updated": {"$gte": start_date, "$lt": end_date},
            "embedding": {"$exists": True} # Assure qu'on ne prend que les articles modifiés
        },
        # Projection pour n'inclure que les champs nécessaires (meilleure performance)
        {'_id': 0, 'embedding': 1, 'label': 1} 
    ))
    
    if not articles_prod:
        print("[ALERTE] Aucune donnée de production trouvée pour le monitoring.")
        # Vous pouvez logguer un statut de succès pour ne pas mettre le DAG en échec
        return
        
    # Création du DataFrame de production
    embeddings_prod = [article['embedding'] for article in articles_prod]
    
    # Le nombre de features est la dimension de l'embedding (ex: 384)
    # Nous utilisons la dimension du premier embedding comme référence
    feature_count = len(embeddings_prod[0]) if embeddings_prod else 0

    df_production = pd.DataFrame(
        embeddings_prod,
        columns=[f"feature_{i}" for i in range(feature_count)]
    )
    
    # Le DataFrame de production n'a PAS besoin de la colonne 'target'
    # car DataDriftPreset se concentre sur les features, et target_drift se concentre sur le label.
    # Dans ce cas, nous faisons juste Data Drift sur les features (embeddings)
    
    print(f"Données de référence: {len(df_reference)} | Données de production (1j): {len(df_production)}")

    # 4. Exécution du rapport Evidently (Drift)
    # On définit le mapping pour que Evidently sache quelles colonnes analyser
    column_mapping = ColumnMapping(
        target=None, # On ne surveille pas le label ici (on utilise que les features)
        numerical_features=[f"feature_{i}" for i in range(feature_count)],
        categorical_features=[]
    )
    
    #data_drift_report = Report(metrics=[DataDriftPreset()])
 
        # La référence DOIT correspondre à la production (pas de 'target' si on l'exclut)
    if 'target' in df_reference.columns:
        df_reference_features = df_reference.drop('target', axis=1)
    else:
        df_reference_features = df_reference

    data_drift_report.run(
    reference_data=df_reference_features,
    current_data=df_production,
    column_mapping=column_mapping
    )
    
    # 5. Sauvegarde et/ou Envoi du Rapport
    #  Sauvegarde locale pour la simplicité MLOps
    report_path = f"{MLFLOW_LOCAL}/drift_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    data_drift_report.save_html(report_path)
    
    # Logguer le rapport sous dans MLflow 
    mlflow.set_experiment("evidently_monitoring")
    with mlflow.start_run(run_name=f"drift_check_{datetime.now().strftime('%Y-%m-%d')}"):
        mlflow.log_artifact(report_path, artifact_path="daily_drift_reports")
        
        # Logguer le statut du drift
        #drift_detected = data_drift_report.as_dict()['metrics'][0]['result']['dataset_drift']
        report_dict = data_drift_report.as_dict()
        #dataset_drift=None
        #for metric in report_dict['metrics']:
            #if metric['metric'] == 'DataDriftPreset':
               # dataset_drift = metric['result']['dataset_drift']
               # break
        dataset_drift = report_dict['metrics'][0]['result']['dataset_drift']
               
        mlflow.log_metric("drift_detected", int(dataset_drift))
        print(f"Drift détecté: {dataset_drift}")
    print(f"Rapport sauvegardé et loggué dans MLflow: {report_path}")

    tests = TestSuite(tests=[DataStabilityTestPreset(), DataDriftTestPreset()])
    tests.run(
        reference_data=df_reference_features,
        current_data=df_production,
        column_mapping=column_mapping
    )
    tests_path = f"{MLFLOW_LOCAL}/drift_tests_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    tests.save_json(tests_path)
    mlflow.log_artifact(tests_path, artifact_path="daily_drift_tests")
    print(f"Résultats des tests Evidently sauvegardés: {tests_path}")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
        dag_id="evidently_daily_drift_monitoring",
        default_args=default_args,
        start_date=datetime(2025, 1, 1),
        schedule_interval=timedelta(hours=24), # Tous les jours
        catchup=False,
        tags=["evidently", "monitoring"],
) as dag:
    
    run_drift_check_task = PythonOperator(
        task_id="check_data_drift",
        python_callable=run_drift_check,
        provide_context=True,
    )