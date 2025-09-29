FROM jenkins/jenkins:lts
USER root
RUN apt-get update && apt-get install -y \
    docker.io \
    # Ajoutez python3 et python3-pip ici si nécessaire pour les tests Jenkins
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Ajoutez l'utilisateur jenkins au groupe docker
RUN usermod -a -G docker jenkins

USER jenkins