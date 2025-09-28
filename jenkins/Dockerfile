FROM jenkins/jenkins:lts

# Installez le client Docker (seulement le client, pas le démon)
USER root
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Ajoutez l'utilisateur jenkins au groupe docker (le client docker s'exécutera sous root, mais c'est une bonne pratique)
RUN usermod -a -G docker jenkins

USER jenkins