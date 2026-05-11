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