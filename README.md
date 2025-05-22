# 🚀 Data Pipeline avec Apache Airflow, FastAPI, Streamlit, MongoDB, PostgreSQL & MLflow

Ce projet met en place une architecture complète de data pipeline basée sur Apache Airflow pour l'orchestration, FastAPI pour l'accès aux données, Streamlit pour la visualisation, MongoDB et PostgreSQL pour le stockage, et MLflow pour le suivi des expériences de Machine Learning.

## 📦 Services inclus

| Service               | Port    | Description |
|-----------------------|---------|-------------|
| Airflow Webserver     | `8080`  | Interface d'administration d'Airflow |
| Airflow Scheduler     | -       | Planification des DAGs |
| Airflow Worker        | -       | Exécution des tâches avec Celery |
| Airflow Triggerer     | -       | Gestion des triggers (ex. capteurs) |
| PostgreSQL            | -       | Base de données utilisée par Airflow |
| Redis                 | `6379`  | Broker Celery pour Airflow |
| MongoDB               | `27017` | Base de données utilisée par l'API backend |
| FastAPI               | `8500`  | Backend API pour accéder aux données |
| Streamlit             | `8501`  | Interface web de visualisation |
| MLflow                | `5050`  | Suivi des expérimentations ML |

---

## 🏗️ Structure des dossiers

```bash
.
├── airflow/              # Dossiers Airflow (DAGs, logs, plugins)
├── backend/              # Code de l'API FastAPI
├── frontend/             # Interface Streamlit
├── mlruns/               # Dossiers de suivi MLflow
├── .env                  # Fichier d’environnement
├── docker-compose.yaml   # Configuration Docker complète
├── import_env_to_airflow.py  # Script d'import des variables d'env dans Airflow
