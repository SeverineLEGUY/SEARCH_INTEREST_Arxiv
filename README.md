# 🚀 Data Pipeline avec Apache Airflow, FastAPI, Streamlit, MongoDB, PostgreSQL & MLflow

Ce projet met en place une **architecture complète de MLOps** pour l’automatisation du cycle de vie d’un modèle de Machine Learning appliqué aux articles scientifiques publiés sur l’**API ArXiv en temps réel**.

Concrètement, le pipeline :

-  **Récupère automatiquement** les nouveaux articles publiés sur l’API ArXiv ;  
-  **Stocke et organise** les données brutes dans plusieurs bases :  
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

```

## 🚀 Initialisation et Lancement

### 1️⃣ Cloner le dépôt
```bash
git clone https://github.com/SeverineLEGUY/SEARCH_INTEREST_Arxiv.git
cd SEARCH_INTEREST_Arxiv
```

### 2️⃣ Configurer les variables d’environnement

Créer un fichier `.env` à partir du template fourni :  
```bash
cp .env.template .env

# ARXIV
ARXIV_CATEGORY="cs.AI"
ARXIV_START_DATE="2025-01-01T00:00:00Z"

# Redis
REDIS_HOST="airflow-run-redis"
REDIS_PORT="6379"
REDIS_TRAINQ="arxiv_classifier_train_test"
REDIS_CLASSQ="arxiv_classifier"

# MongoDB
MONGO_URI="mongodb://backend-run-mongodb:27017/"
MONGO_DB="arxiv"
MONGO_SUMMARIZE="arxiv_summaries"
MONGO_CLASSIFY="arxiv_classifications"

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5050

# API Keys
MISTRAL_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

```
### 3️⃣ Construire et lancer les services
      ```bash
       docker compose up --build
       docker ps
  ```     
### 4️⃣ Accéder aux interfaces

* Airflow → [http://localhost:8082](http://localhost:8082) ↗️
* FastAPI → [http://localhost:8500/docs](http://localhost:8500/docs) ↗️
* Streamlit → [http://localhost:8501](http://localhost:8501) ↗️
* MLflow → [http://localhost:5050](http://localhost:5050) ↗️
* Jenkins → [http://localhost:8080](http://localhost:8080) ↗️



### 🗂️ DAGs et ordre d’exécution

Lancez manuellement les DAGs d'Entraînement 
   - 1. cleanup_redis_and_mongo → Vide les bases Redis et MongoDB
   - 2. arxiv_to_redis_train →  Récupère un échantillon d’articles depuis l’API ArXiv
   - 3. arxiv_training → Entraîne le modèle de classification (LLM Mistral) et enregistre la version du modèle dans MLflow.  
Puis activez les trois DAGs de Production pour lancement auto selon la frequence indiqué
   - 4. arxiv_to_redis (8 minutes)  → recupère les nouveaux articles Arxiv pour les mettre dans la queue redis
   - 5. summarize_arxiv_article (30 min) → résumé automatique des articles à l’aide du LLM Mistral
   - 6. classify_arxiv_article (45 min) → Catégorise les articles par domaine scientifique 
   - 7. evidently_daily_drift_monitoring : suivi quotidie de derive de données et de performance du modèle en production.  

⚠️ Remarque : l’ordre doit être respecté. Les dépendances entre DAGs peuvent être configurées dans Airflow.