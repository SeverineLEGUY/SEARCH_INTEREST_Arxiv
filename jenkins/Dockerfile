FROM jenkins/jenkins:lts
USER root
RUN apt-get update && apt-get install -y \
    docker.io \
    # Ajoutez python3 et python3-pip ici si nécessaire pour les tests Jenkins
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/docker /usr/local/bin/docker

COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

# Ajoutez l'utilisateur jenkins au groupe docker
RUN usermod -a -G docker jenkins
USER jenkins