# Docker Commands

Created by: aranya majumdar

# Background

**Docker** is an **open-source platform** that enables developers to build, deploy, and run applications using **containers**.  It packages software into standardized, lightweight units that include the application code, runtime, system tools, libraries, and dependencies, ensuring the application runs consistently across different computing environments.

# Common Commands

### Shows all the docker commands

```docker
docker
```

### Shows the version of the docker

```docker
docker -v
```

### To pull the docker image

```docker
docker pull <image name>
```

### To get the list of docker images

```docker
docker images
```

### To create a container from an image

```docker
docker run <image name>
```

### To create and run container in interactive mode

```docker
docker run -it <image name>
```

### This shows the list of containers that we have created

```docker
docker ps -a
```

### This shows the running containers

```docker
docker ps
```

### To restart an existing container

```docker
docker start <container name or container id>
```

### To stop running container

```docker
docker stop <container name/id>
```

### To remove or delete the image

```docker
docker rmi <image name/id>
```

### To delete the container

```docker
docker rm <container name/id>
```

### To pull the specific version of the image

```docker
docker pull <image name:version>
```

### To run the docker image in detach mode

```docker
docker run -d <image name>
```

### To provide a custom name to the container

```docker
docker run --name <container name>
```

### To run MySQL image with a root password

```docker
docker run -d -e MYSQL_ROOT_PASSWORD=<password> <image name>
```

### port binding

```docker
docker run -p <host port>:<container port> <image name>
```

### To access the logs of a specific container

```docker
docker logs <container id/name>
```

### To check the container details

```docker
docker inspect <container id>
```

### To run a command inside the existing running container

```docker
docker exec -it <container id>/bin/bash
```

### To check the available networks

```docker
docker network ls
```

### To create a new network

```docker
docker network create <network name>
```

### To create the docker container with yml file

```docker
docker compose -f <filename>.yml up -d
```

### To remove or delete the containers

```docker
docker compose -f <filename>.yml down
```

### To build docker image of the local app

```docker
docker build -t <appname>:tag .
```

### To remove the docker login credentials

```docker
docker logout
```

### To login to Docker Hub via command prompt

```docker
docker login -u <username>
```

### To create and map the volume to the container

```docker
docker run -it -v <absolute path of host data folder>:<path of data folder in container> <image name>
```

### To check the available volumes

```docker
docker volume ls
```

### To create a custom volume

```docker
docker volume create <volume name> 
```

### To remove or delete a volume

```docker
docker volume rm <volume name>
```

### These are called named volumes

```docker
docker run -v <volume name>:<container directory>
```

### These are called anonymous volumes

```docker
docker run -v <mount path>
```

### This is how we bind mount our local host

```docker
docker run -v <host directory>:<container directory>
```

### To delete unused volumes

```docker
docker volume prune
```

### This line of code prevents creation of Python cache files or .pyc files

```docker
ENV PYTHONDONTWRITEBYTECODE = 1
```

### Shows logs or output immediately

```docker
ENV PYTHONUNBUFFERED = 1
```

### To install project requirements without caching the dependencies

```docker
pip install --no-cache-dir -r requirements-docker.txt
```

### This command starts our Django development server, opens it up to accept connections from outside the Docker container, and forcefully serves our CSS and JavaScript files even if we are testing in production mode

```docker
python manage.py runserver 0.0.0.0:8000 --insecure
```

### Automatically gathers all CSS, JavaScript, and image files from every app into one centralized folder for production, bypassing the 'are you sure?' confirmation prompt so the Docker build doesn't freeze

```docker
python manage.py collectstatic --noinput
```