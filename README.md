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
| PostgreSQL            | -       | Base de données utilisée par mlFlow |
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
├── mlflow/               # Dossiers de suivi MLflow
├── .env                  # Fichier d’environnement
├── docker-compose.yaml   # Configuration Docker complète
├── import_env_to_airflow.py  # Script d'import des variables d'env dans Airflow

Excellent ! Tous vos services critiques sont Up (y compris Airflow, MLflow, FastAPI et Streamlit), ce qui signifie que votre plateforme est entièrement fonctionnelle. L'anomalie (unhealthy) de MongoDB est mineure à ce stade.

Ordre de Lancement des DAGs Airflow
Vous avez trois étapes principales pour mettre en service votre pipeline (Entraînement, Classification, et Maintenance). L'ordre idéal pour commencer et assurer que le modèle est prêt avant d'être utilisé est le suivant :

Étape 1 : Entraînement Initial du Modèle (Manuel)
C'est l'étape la plus importante à lancer en premier pour que le modèle puisse être utilisé par la suite.

cleanup_redis_and_mongo (Optionnel, mais fortement recommandé)

Action : Exécutez ce DAG d'abord pour vider les files Redis et les collections MongoDB.

But : Assure un environnement de travail propre avant la collecte de nouvelles données.

arxiv_to_redis_train

Action : Lancez ce DAG après le nettoyage.

But : Il va chercher un grand volume d'articles ArXiv (via la date fixe 2024-01-01T00:00:00Z dans fetch_arxiv_train.py) et les pousser dans la file Redis dédiée à l'entraînement (REDIS_TRAINQ).

arxiv_training

Action : Lancez ce DAG immédiatement après que le DAG arxiv_to_redis_train a terminé sa collecte.

But : Il va consommer les articles dans la file Redis, entraîner le modèle de classification (Logistic Regression), et enregistrer le modèle, le LabelEncoder et les métriques dans MLflow.

Étape 2 : Démarrage de la Production (Automatique)
Une fois que le modèle est entraîné (étape 1), vous pouvez activer la classification et la publication.

Activation des DAGs de Production (Commutateur ON)

Vous avez trois DAGs qui sont configurés pour s'exécuter automatiquement à intervalles réguliers (schedule_interval est défini dans le code, mais ils sont en pause à la création par défaut).

Action : Activez (mettez sur ON) les DAGs suivants dans l'interface Airflow (en cliquant sur le commutateur à gauche de leur nom) :

arxiv_to_redis (Toutes les 8 minutes)

classify_arxiv_article (Toutes les 45 minutes)

summarize_arxiv_article (Toutes les 30 minutes)

But :

arxiv_to_redis va chercher les nouveaux articles ArXiv (via la date mise à jour automatiquement) et les met dans la file Redis de classification (REDIS_CLASSQ).

summarize_arxiv_article va prendre les articles et ajouter un résumé français (via l'API Mistral) dans MongoDB.

classify_arxiv_article va prendre les articles, les classifier avec le modèle MLflow, et ajouter le résultat à MongoDB.

Récapitulatif de la Première Connexion
Ouvrez Airflow sur http://localhost:8082. (Identifiants par défaut sont souvent airflow/airflow ou admin/admin).

Lancez les DAGs d'Entraînement (Étape 1) dans l'ordre cleanup → arxiv_to_redis_train → arxiv_training.

Une fois l'entraînement terminé, activez les trois DAGs de Production (Étape 2).

Vous pourrez ensuite consulter les résultats :

Modèle entraîné : http://localhost:5050 (MLflow UI)

Données traitées : http://localhost:8501 (Streamlit UI)