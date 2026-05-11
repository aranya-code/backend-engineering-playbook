# Docker Notes

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