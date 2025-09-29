FROM python:3.9-slim

# Mise à jour du système et installation des utilitaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# CORRECTION : Copier le fichier de dépendances SPECIFIQUE aux tests/CI
# Le chemin source est relatif à la racine du projet (le contexte '.')
COPY jenkins/requirements.txt requirements.txt 

# Installer les dépendances Python
# Cette étape est mise en cache tant que requirements.txt ne change pas.
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script ETL principal
COPY fetch_arxiv_unitaire.py fetch_arxiv_unitaire.py

# Définir l'entrée principale du conteneur
ENTRYPOINT ["python", "/app/fetch_arxiv_unitaire.py"]