FROM apache/airflow:2.8.3
USER root

# Mise à jour et installation des dépendances système utiles
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Set the working directory to the user's home directory
WORKDIR /opt/airflow

RUN mkdir mlflow && chmod -R 777 mlflow

# Try and run pip command after setting the user with `USER user` to avoid permission issues with Python
RUN pip install --no-cache-dir --upgrade pip

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=airflow dags/*.py dags/
COPY --chown=airflow requirements.txt requirements.txt

# Install any other Python dependencies (e.g., from requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt 
