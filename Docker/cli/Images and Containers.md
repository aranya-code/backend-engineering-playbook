# Images and Containers

---

### Downloads an image from a registry.

```bash
docker pull <image>
```

### Downloads a specific image version.

```bash
docker pull <image:tag>
```

### Lists local images.

```bash
docker images
```

### Creates and starts a container.

```bash
docker run <image>
```

### Runs a container interactively.

```bash
docker run -it <image>
```

### Runs a container in detached mode.

```bash
docker run -d <image>
```

### Assigns a custom container name.

```bash
docker run --name <container>
```

### Maps a host port to a container port.

```bash
docker run -p <host>:<container> <image>
```

### Lists running containers.

```bash
docker ps
```

### Lists all containers.

```bash
docker ps -a
```

### Starts an existing container.

```bash
docker start <container>
```

### Stops a running container.

```bash
docker stop <container>
```

### Removes a container.

```bash
docker rm <container>
```

### Removes an image.

```bash
docker rmi <image>
```

### Displays container logs.

```bash
docker logs <container>
```

### Opens a shell inside a running container.

```bash
docker exec -it <container> /bin/bash
```

### Displays container details.

```bash
docker inspect <container>
```

### Lists running processes inside a container.

```bash
docker top <container>
```

### Displays live resource usage.

```bash
docker stats <container>
```

### Shows port mappings.

```bash
docker port <container>
```
