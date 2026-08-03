# Images and Containers

## Overview
Docker images and containers are the fundamental building blocks of Docker. Images are the immutable, read-only templates that contain the application and its dependencies, while containers are the running instances of those images. This guide covers the essential commands for managing the lifecycle of both images and containers, from pulling and running to inspecting and removing them.

## Common Commands

| Command | Description |
|---|---|
| `docker pull <image>` | Pulls an image or a repository from a registry |
| `docker pull <image:tag>` | Pulls a specific version of an image |
| `docker images` | Lists all local images |
| `docker run <image>` | Creates and starts a container from an image |
| `docker run -it <image>` | Runs a container in interactive mode |
| `docker run -d <image>` | Runs a container in detached mode (background) |
| `docker run --name <container>` | Assigns a custom name to the container |
| `docker run -p <host>:<container> <image>` | Maps a host port to a container port |
| `docker ps` | Lists running containers |
| `docker ps -a` | Lists all containers (running and stopped) |
| `docker start <container>` | Starts one or more stopped containers |
| `docker stop <container>` | Stops one or more running containers |
| `docker rm <container>` | Removes one or more containers |
| `docker rmi <image>` | Removes one or more images |
| `docker logs <container>` | Fetches the logs of a container |
| `docker exec -it <container> /bin/bash` | Runs a command in a running container |
| `docker inspect <container>` | Returns low-level information on Docker objects |
| `docker top <container>` | Displays the running processes of a container |
| `docker stats <container>` | Displays a live stream of container resource usage statistics |
| `docker port <container>` | Lists port mappings or a specific mapping for the container |
| `docker restart <container>` | Restarts one or more containers |
| `docker kill <container>` | Kills one or more running containers instantly |
| `docker cp <container>:<path> <host-path>` | Copies files/folders between a container and the local filesystem |
| `docker diff <container>` | Inspects changes to files or directories on a container's filesystem |
| `docker tag <image> <new-tag>` | Creates a tag TARGET_IMAGE that refers to SOURCE_IMAGE |
| `docker push <image>` | Pushes an image or a repository to a registry |
| `docker attach <container>` | Attaches local standard input, output, and error streams to a running container |
| `docker rename <old> <new>` | Renames a container |
| `docker wait <container>` | Blocks until one or more containers stop, then prints their exit codes |
| `docker create <image>` | Creates a new container without starting it |
| `docker export` | Exports a container's filesystem as a tar archive |
| `docker import` | Imports the contents from a tarball to create a filesystem image |
| `docker history <image>` | Shows the history of an image |
| `docker save` | Saves one or more images to a tar archive |
| `docker load` | Loads an image from a tar archive or STDIN |

## Command Breakdown

### `docker run` - The Swiss Army Knife
The `docker run` command is the most frequently used command for managing containers. It creates a writeable container layer over the specified image and then starts it using the specified command.

**Important Flags:**
- `-d`, `--detach`: Run container in background and print container ID.
- `-i`, `--interactive`: Keep STDIN open even if not attached.
- `-t`, `--tty`: Allocate a pseudo-TTY. (Usually combined as `-it`).
- `--name`: Assign a custom name to the container for easy reference.
- `-p`, `--publish`: Publish a container's port(s) to the host (e.g., `-p 8080:80`).
- `-v`, `--volume`: Bind mount a volume (e.g., `-v /host/path:/container/path`).
- `--rm`: Automatically remove the container when it exits.
- `-e`, `--env`: Set environment variables (e.g., `-e POSTGRES_PASSWORD=secret`).
- `--env-file`: Read in a file of environment variables.
- `--network`: Connect a container to a network.
- `--restart`: Restart policy to apply when a container exits (`no`, `on-failure`, `always`, `unless-stopped`).
- `--memory`, `-m`: Memory limit (e.g., `--memory=512m`).
- `--cpus`: Number of CPUs (e.g., `--cpus=1.5`).
- `-w`, `--workdir`: Working directory inside the container.
- `--entrypoint`: Overwrite the default ENTRYPOINT of the image.

## Comparison Tables

### `docker run` vs `docker start`
| Feature | `docker run` | `docker start` |
|---|---|---|
| Action | Creates a **new** container and starts it | Resumes an **existing**, stopped container |
| State | Starts from scratch (image default state) | Retains state from when it was stopped |
| Usage | Initializing a new workload | Bringing a workload back up |

### `docker exec` vs `docker attach`
| Feature | `docker exec` | `docker attach` |
|---|---|---|
| Process | Starts a **new** process inside the container | Connects to the **primary process** (PID 1) |
| Effect of Exit | Exiting shell does not stop the container | Exiting (Ctrl+C) stops the container |
| Usage | Debugging, running secondary scripts | Viewing main application logs/input |

### `docker stop` vs `docker kill`
| Feature | `docker stop` | `docker kill` |
|---|---|---|
| Signal | Sends `SIGTERM`, waits a grace period, then `SIGKILL` | Sends `SIGKILL` immediately |
| Graceful | Yes (gives app time to clean up) | No (terminates process instantly) |
| Usage | Standard way to stop containers | When container is unresponsive |

### `docker rm` vs `docker rmi`
| Feature | `docker rm` | `docker rmi` |
|---|---|---|
| Target | Containers | Images |
| Condition | Container must be stopped (unless `-f` is used) | Image cannot be in use by any container |
| Usage | Cleaning up old container instances | Cleaning up disk space from images |

## Practical Examples

### Viewing Running Containers (`docker ps`)
```bash
docker ps
```
Expected output:
```text
CONTAINER ID   IMAGE     COMMAND                  CREATED          STATUS          PORTS                  NAMES
f92a34493393   nginx     "/docker-entrypoint.…"   2 minutes ago    Up 2 minutes    0.0.0.0:8080->80/tcp   web-server
```
* **CONTAINER ID**: Unique alphanumeric ID for the container.
* **IMAGE**: The image used to create the container.
* **COMMAND**: The entrypoint or command executed on startup.
* **CREATED**: When the container was created.
* **STATUS**: Current state (e.g., Up, Exited).
* **PORTS**: Host to container port mappings.
* **NAMES**: The human-readable name assigned to the container.

### Listing Images (`docker images`)
```bash
docker images
```
Expected output:
```text
REPOSITORY   TAG       IMAGE ID       CREATED        SIZE
nginx        latest    605c77e624dd   2 weeks ago    141MB
ubuntu       20.04     ba6acccedd29   2 months ago   72.8MB
```
* **REPOSITORY**: Name of the image repository.
* **TAG**: The specific version/tag of the image.
* **IMAGE ID**: Unique identifier for the image.
* **CREATED**: When the image was built.
* **SIZE**: Total size of the image.

### Monitoring Container Resources (`docker stats`)
```bash
docker stats
```
Expected output:
```text
CONTAINER ID   NAME         CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS
f92a34493393   web-server   0.00%     2.871MiB / 7.766GiB   0.04%     1.51kB / 0B       0B / 8.19kB       3
```
* Shows live usage of CPU, memory, network, and disk I/O for running containers.

### Running Nginx with Port Mapping
```bash
docker run -d --name my-nginx -p 8080:80 nginx
```
Expected output:
```text
4a9c8b7d6e5f4c3b2a1...
```
* Runs an Nginx web server in the background. Accessing `http://localhost:8080` on the host will route to port `80` inside the container.

### Copying Files In and Out of a Container
Copy a local configuration file into a running container:
```bash
docker cp ./nginx.conf my-nginx:/etc/nginx/nginx.conf
```
Copy a generated log file from the container to the host:
```bash
docker cp my-nginx:/var/log/nginx/access.log ./access.log
```

## Real-World Use Cases
- **Local Development**: Using `docker run -v` to mount source code into a container, allowing hot-reloading without rebuilding images.
- **Background Services**: Running databases (Redis, PostgreSQL) locally with `docker run -d` and specific `-p` mappings for local testing.
- **Troubleshooting**: Using `docker exec -it <container> /bin/bash` (or `sh`) to dive into a misbehaving container to check file permissions, network connectivity, or missing dependencies.
- **Cleanup Automation**: Scripting `docker rm $(docker ps -a -q)` to clear out stopped containers after a CI pipeline finishes.

## Common Mistakes
- **Forgetting `--rm` for short-lived containers**: Leaves stopped containers littering the system, consuming disk space.
- **Not naming containers**: Let's Docker generate random names (e.g., `focused_turing`), making it hard to target them with subsequent commands. Always use `--name`.
- **Port Conflicts**: Trying to map `-p 8080:80` when another service on the host is already using port `8080`.
- **Removing a running container**: Using `docker rm` fails on running containers. You must `docker stop` first or use `docker rm -f`.
- **Assuming `docker exec` works on stopped containers**: You can only `exec` into a container that is currently `Up`.

## Best Practices
- **Use meaningful tags**: Don't rely solely on `:latest`. Use specific version tags (e.g., `node:18.16.0-alpine`) for reproducibility.
- **Limit Resources**: In production, always use `--memory` and `--cpus` to prevent a single container from starving the host system.
- **Use Detached Mode**: Run long-lived services with `-d` and check their output via `docker logs -f <container>`.
- **Clean up regularly**: Use `docker system prune` occasionally, or aggressively use `--rm` when running temporary tools.

## Interview Tips

- **Q: What exactly happens when you execute `docker run <image>`?**
  A: Docker first checks if the image exists locally. If not, it pulls it from the registry. Then it creates a new container layer over the image, allocates a filesystem, sets up networking/IP, and executes the default command defined in the image (CMD/ENTRYPOINT).
- **Q: What is the difference between CMD and ENTRYPOINT in a Dockerfile?**
  A: `ENTRYPOINT` configures the container to run as an executable (it cannot be easily overridden), while `CMD` provides default arguments to the entrypoint (or a default command if no entrypoint is set) which can be easily overridden at the end of the `docker run` command.
- **Q: How do you debug a container that crashes immediately upon starting?**
  A: First, check `docker logs <container>` to see the application error. If it exits too fast, you can override the entrypoint to keep it alive for inspection: `docker run -it --entrypoint /bin/sh <image>`.
- **Q: What is the difference between `docker stop` and `docker kill`?**
  A: `docker stop` sends a `SIGTERM` signal, allowing the application to shut down gracefully and save state. `docker kill` sends a `SIGKILL`, forcefully terminating the process immediately.

## Related Topics
- [Networking](05-%20Networking.md)
- [Volumes and Bind Mounts](04-%20Volumes%20and%20Bind%20Mounts.md)
- [Dockerfile](03-%20Dockerfile.md)
- [Docker Compose](06-%20Docker%20Compose.md)

## Key Takeaways
- Images are read-only templates; containers are running instances of images.
- `docker run` is a versatile command that combines image pulling, container creation, and startup.
- Differentiate between creating new instances (`run`) and managing existing ones (`start`, `stop`, `exec`).
- Always name your containers and be mindful of port mappings to avoid conflicts.
- Graceful termination (`stop`) is preferred over forceful termination (`kill`).
