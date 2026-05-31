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

### To inspect the network status

```docker
docker network insepct
```

### To attach container to a network

```docker
docker network connect
```

### To detach container to a network

```docker
docker network disconnect
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

```docker
docker run -d --name mysql-new -e MYSQL_ALLOW_EMPTY_PASSWORD=TRUE -v mysql-db:/var/lib/mysql mysql 
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

### To cleanup everything that is not running

```jsx
docker system prune
```

### To cleanup dangling images

```jsx
docker image prune
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

### To give the container a specific name

```docker
docker run -p 80:80 --name <Container name>
```

### To list the processes that are running inside a container

```docker
docker top <container name>
```

### To get the configuration of container

```docker
docker inspect <container name/id>
```

### To get performance stats of a container

```docker
docker stats <container name/id>
```

### To check the port details of a container

```docker
docker port <container id>
```

### To initialize the Docker Swarm

```docker
docker swarm init
```

### To check all the swarm nodes

```docker
docker node ls
```

### To create docker swarm service

```docker
docker service create <image name>
```

### To list all the services

```docker
docker service ls
```

### To update swarm service config

```docker
docker service update <service name or id> --<new setting>
```

### To create a swarm network

```docker
docker network create --driver overlay <network name>
```

### To create a Stack file

```docker
docker stack deploy -c <yml file name> <stack name>
```

### To check the stacks list

```docker
docker stack ls
```

### To check the tasks status of a stack

```docker
docker stack ps <stack name>
```

### To show the stack services

```docker
docker stack services <stack name>
```

## To inspect Stack services

```docker
docker service ls
```

## To update a Stack

```docker
docker stack deploy -c docker-compose.yml myapp
```

## To remove a Stack

```bash
docker stack rm myapp
```

## To view Stack logs

```bash
docker service logs myapp_web
```

## To create a Secret

```bash
echo "mypassword" | docker secret create db_password -
```

## To list all Secrets

```bash
docker secret ls
```

## To inspect a Secret

```bash
docker secret inspect db_password
```

## To create a service with a Secret

```bash
docker service create \\
  --name mysql \\
  --secret db_password \\
  mysql
```

## To remove a Secret

```bash
docker secret rm db_password
```

## To view mounted Secrets inside a container

```bash
ls /run/secrets
```

## To read a Secret

```bash
cat /run/secrets/db_password
```

---

# Docker Health Checks – Common Commands

## To run a container with Health Check

```bash
docker run -d \\
  --health-cmd="curl -f <http://localhost> || exit 1" \\
  nginx
```

## To check container health status

```bash
docker ps
```

## To inspect health details

```bash
docker inspect <container_id>
```

## To show only health status

```bash
docker inspect \\
--format='{{json .State.Health}}' \\
<container_id>
```

## Dockerfile Health Check

```bash
HEALTHCHECK --interval=30s \\
--timeout=5s \\
--retries=3 \\
CMD curl -f <http://localhost> || exit 1
```

## Disable Health Check

```console
$ docker run --no-healthcheck nginx
```

## Health Check in Compose

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "<http://localhost>"]
  interval: 30s
  timeout: 5s
  retries: 3
```