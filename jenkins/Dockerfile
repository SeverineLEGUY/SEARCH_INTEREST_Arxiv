FROM jenkins/jenkins:lts

USER root

# Installer Docker client + Python3 + pip
RUN apt-get update && apt-get install -y \
    docker.io \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.txt .

# Installer dépendances Python
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Ajouter l'utilisateur jenkins au groupe docker
RUN usermod -a -G docker jenkins

# Repasser à l'utilisateur Jenkins
USER jenkins