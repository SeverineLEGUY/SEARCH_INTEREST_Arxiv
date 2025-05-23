import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("arxiv_summarization")

with mlflow.start_run():
    mlflow.log_param("model", "facebook/bart-large-cnn")
    mlflow.log_metric("dummy_score", 0.95)
    mlflow.set_tag("stage", "test")

    # Enregistrement d'un modèle vide comme exemple
    with open("dummy_model.txt", "w") as f:
        f.write("dummy model")
    mlflow.log_artifact("dummy_model.txt")
