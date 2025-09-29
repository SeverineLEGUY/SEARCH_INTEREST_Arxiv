FROM python:3.9-slim

# Mettre à jour et installer les dépendances système de base
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail pour l'application
WORKDIR /app

# Copier les fichiers de dépendance pour la couche de cache
COPY requirements.txt .

# Installer les dépendances Python
# ATTENTION: requirements.txt contient 'apache-airflow' qui est lourd et inutile ici.
# Pour le pipeline Jenkins simple (sans Airflow), utilisez un requirements.txt filtré
# ou installez uniquement les modules nécessaires (requests, boto3, pytest)
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
# Le contexte de construction est la racine du projet, donc on copie les dossiers pertinents
COPY jenkins/tests/fetch_arxiv_unitaire.py jenkins/tests/fetch_arxiv_unitaire.py
# Si d'autres modules sont nécessaires, ajouter 'COPY . .' ou les copier explicitement

# Définir l'entrée principale du conteneur (pour la documentation, Jenkins l'écrase)
ENTRYPOINT ["python", "/app/jenkins/tests/fetch_arxiv_unitaire.py"]