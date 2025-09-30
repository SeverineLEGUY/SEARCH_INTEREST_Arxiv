# 🚀 Data Pipeline avec Apache Airflow, FastAPI, Streamlit, MongoDB, PostgreSQL & MLflow

Ce projet met en place une **architecture complète de MLOps** pour l’automatisation du cycle de vie d’un modèle de Machine Learning appliqué aux articles scientifiques publiés sur l’**API ArXiv en temps réel**.

Concrètement, le pipeline :

- 📥 **Récupère automatiquement** les nouveaux articles publiés sur l’API ArXiv ;  
- 🗄️ **Stocke et organise** les données brutes dans plusieurs bases :  
        - Redis pour le cache  
        - MongoDB pour le NoSQL  
        - PostgreSQL pour le relationnel  
- 🏷️ **Catégorise** les articles selon leurs domaines scientifiques ;  
- 📝 **Génère un résumé et une traduction multilingue** grâce à un **LLM Mistral** ;  
- 🌐 **Expose les résultats** via :  
        - une API REST (FastAPI)  
        - une interface utilisateur interactive (Streamlit)  
- 📊 **Suit et versionne les modèles** avec **MLflow** (traçabilité des expériences, métriques, artefacts) ;  
- ⚙️ **Orchestre et automatise** toutes les étapes avec **Airflow** (extraction, transformation, stockage, entraînement, déploiement) ;  
- 🚀 **Déploie la solution en continu** grâce à **Docker** + **Jenkins/GitHub Actions** (CI/CD) ;  
- 👀 **Supervise le comportement en production** avec **Evidently** (suivi de la dérive de données et des performances).  


## 📦 Services inclus

| Service               | Port    | Description |
|-----------------------|---------|-------------|
| Airflow Webserver     | `8082`  | Interface d'administration d'Airflow |
| Airflow Scheduler     | -       | Planification et orchestration des DAGs |
| Airflow Worker        | -       | Exécution des tâches distribuées via Celery |
| Airflow Triggerer     | -       | Gestion des triggers et capteurs (sensors) |
| PostgreSQL            | `5432`  | Base de données relationnelle (Airflow + MLflow metadata) |
| Redis                 | `6379`  | Broker Celery pour la communication entre Scheduler et Workers |
| MongoDB               | `27017` | Base de données NoSQL utilisée par l’API backend |
| FastAPI               | `8500`  | Backend API pour accéder aux données traitées |
| Streamlit             | `8501`  | Interface web pour la visualisation et l’interaction utilisateur |
| MLflow                | `5050`  | Suivi et versionnage des expériences ML (métriques, artefacts, modèles) |
| Jenkins               | `8080`  | Serveur CI/CD pour l’intégration et le déploiement continu |
| Evidently             | -       | Monitoring des modèles en production (dérive de données, qualité, métriques) |

---

## 🏗️ Structure des dossiers

```bash
.
├── airflow/                  # Dossiers Airflow (DAGs, logs, plugins)
├── backend/                  # Code de l'API FastAPI
├── frontend/                 # Interface Streamlit
├── jenkins                   # Pipeline CI/CD 
├── mlflow/                   # Dossiers de suivi MLflow
├── .env                      # Fichier d’environnement
├── docker-compose.yaml       # Configuration Docker complète
├── import_env_to_airflow.py  # Script d'import des variables d'env dans Airflow

