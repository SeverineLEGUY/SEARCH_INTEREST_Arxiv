FROM python:3.9-slim

# Mettre à jour et installer les dépendances système de base (y compris curl pour les dépendances réseau)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail pour l'application dans le conteneur
WORKDIR /app

# Copier les fichiers de dépendance pour la couche de cache Docker
# (Nécessite que requirements.txt soit accessible dans le contexte de build)
COPY requirements.txt .

# Installer les dépendances Python (boto3, requests, etc.)
# Note : Cette étape utilise les packages de requirements.txt, même si certains ne sont pas requis
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script ETL nécessaire
# Ceci résout l'erreur de "file not found", car le chemin source est complet
# et le contexte de construction doit être la racine du projet (voir Jenkinsfile corrigé).
COPY jenkins/tests/fetch_arxiv_unitaire.py jenkins/tests/fetch_arxiv_unitaire.py

# Définir le point d'entrée par défaut (pour la documentation, Jenkins écrase cette commande)
ENTRYPOINT ["python", "/app/jenkins/tests/fetch_arxiv_unitaire.py"]