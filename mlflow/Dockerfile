FROM python:3.10-slim-bullseye

# Mise à jour et installation des dépendances système utiles
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /mlflow && chmod -R 777 /mlflow

# Set the working directory to the user's home directory
WORKDIR /mlflow

# Try and run pip command after setting the user with `USER user` to avoid permission issues with Python
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /mlflow

# Install MLflow
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port we run MLflow
EXPOSE 5050

# Définit la commande par défaut pour lancer MLflow en mode serveur local
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5050", "--default-artifact-root", "/mlflow/mlruns", "--dev"]
