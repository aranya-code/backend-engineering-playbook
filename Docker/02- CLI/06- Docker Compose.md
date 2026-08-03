# Docker Compose

## Overview
Docker Compose is a tool for defining and running multi-container Docker applications using a YAML configuration file. The modern CLI uses the `docker compose` plugin syntax rather than the older standalone `docker-compose` binary, providing seamless integration with the core Docker CLI and better performance.

## Common Commands
| Command | Description |
|---|---|
| `docker compose up` | Builds, (re)creates, starts, and attaches to containers for a service. |
| `docker compose down` | Stops containers and removes containers, networks, volumes, and images created by `up`. |
| `docker compose -f docker-compose.yml up -d` | Uses a specific Compose file and starts containers in the background. |
| `docker compose -f docker-compose.yml down` | Stops and removes containers defined in a specific Compose file. |
| `docker compose ps` | Lists all running containers for the current Compose project. |
| `docker compose logs` | Views output from containers. |
| `docker compose build` | Builds or rebuilds services. |
| `docker compose exec <service> <cmd>` | Executes a command in a running container. |
| `docker compose run <service> <cmd>` | Runs a one-off command on a service. |
| `docker compose start` | Starts existing containers for a service. |
| `docker compose stop` | Stops running containers without removing them. |
| `docker compose restart` | Restarts all stopped and running services. |
| `docker compose pull` | Pulls images for services defined in the Compose file. |
| `docker compose top` | Displays the running processes for all services. |
| `docker compose config` | Validates and views the Compose file to ensure formatting is correct. |

### Command Comparisons

**`docker compose up` vs `docker compose start`**
| Feature | `docker compose up` | `docker compose start` |
|---|---|---|
| **Action** | Creates and starts containers, networks, and volumes. | Only starts pre-existing containers. |
| **When to use** | Initializing an environment or applying configuration changes. | Resuming services that were previously stopped. |

**`docker compose down` vs `docker compose stop`**
| Feature | `docker compose down` | `docker compose stop` |
|---|---|---|
| **Action** | Stops and completely removes containers and default networks. | Halts container processes but leaves them intact. |
| **When to use** | Tearing down an environment fully. | Pausing work temporarily to save resources. |

## Command Breakdown

### `docker compose up` Flags
*   `-d` (Detached mode): Runs containers in the background and leaves them running.
*   `--build`: Builds images before starting containers, ensuring the latest code changes are included.
*   `--force-recreate`: Recreates containers even if their configuration and image haven't changed.
*   `--remove-orphans`: Removes containers for services not defined in the current Compose file.
*   `--scale <SERVICE>=<NUM>`: Scales a specific service to the specified number of instances.

## Practical Examples

### Typical Development Workflow
Spin up the environment, check logs, access a shell, and tear it down.
```bash
# Start in the background
docker compose up -d

# Watch logs for all services (tailing)
docker compose logs -f --tail 100

# Execute a shell in the 'backend' service
docker compose exec backend /bin/bash

# Tear down the environment when finished
docker compose down
```

### Rebuilding After Code Changes
When you update a `Dockerfile` or modify dependencies, force a rebuild.
```bash
docker compose up --build
```
Or build without utilizing the cache:
```bash
docker compose build --no-cache
docker compose up -d
```

### Advanced Subcommands
Tear down volumes and remove all images:
```bash
docker compose down --volumes --rmi all
```
Use profiles to start a specific subset of services (e.g., debug tools):
```bash
docker compose --profile debug up
```

### Viewing Expected Output
Running `docker compose ps` shows the status and mapped ports of services.
```text
NAME                IMAGE               COMMAND                  SERVICE             CREATED             STATUS              PORTS
app-backend-1       app-backend         "python manage.py run"   backend             2 minutes ago       Up 2 minutes        0.0.0.0:8000->8000/tcp
app-db-1            postgres:15         "docker-entrypoint.s…"   db                  2 minutes ago       Up 2 minutes        5432/tcp
```

## Real-World Use Cases
*   **Local Development Environments**: Quickly spinning up an application with its dependencies (e.g., database, cache) using a single command without installing them on the host system.
*   **Integration Testing**: Bootstrapping an isolated, ephemeral environment during CI/CD pipelines to run automated test suites against a fully operational stack.
*   **Microservices Orchestration**: Running dozens of interdependent services simultaneously while managing network resolution internally via Docker Compose networks.

## Common Mistakes
*   **Forgetting `--build`**: Modifying code that gets baked into the image but running only `docker compose up`. The containers start using the old cached image. Use `docker compose up --build`.
*   **Orphan Containers**: Changing a service name in the `docker-compose.yml` file, resulting in the old container remaining active. Use `docker compose up --remove-orphans` to clean up.
*   **Compose File Not Found**: Executing commands in a directory that doesn't contain a `compose.yaml` or `docker-compose.yml` file. Always ensure you are in the correct directory or use the `-f` flag.

## Best Practices
*   Use `docker compose down --volumes` periodically to wipe databases and caches if you encounter persistent state issues in local development.
*   Always define specific image tags in your Compose file (e.g., `postgres:15.3`) rather than using `latest` to ensure reproducible environments.
*   Use `.env` files to manage secrets and environment variables, keeping them out of version control and separating them from the `docker-compose.yml` definition.

## Interview Tips
*   **Question**: How does `docker compose` handle networking between services?
    **Answer**: It automatically creates a default bridge network for the project. Services can discover and communicate with each other using their service names as hostnames.
*   **Question**: What happens if you run `docker compose up` while the services are already running?
    **Answer**: By default, it will recreate containers whose configuration or image has changed. Containers with unchanged definitions will be left running untouched.

## Related Topics
- [Dockerfile](03-%20Dockerfile.md)
- [Docker Basics](01-%20Docker%20Basics.md)
- [Networking](05-%20Networking.md)
- [Volumes and Bind Mounts](04-%20Volumes%20and%20Bind%20Mounts.md)

## Key Takeaways
*   `docker compose` replaces the legacy `docker-compose` binary.
*   Use `up` to create/start and `down` to stop/remove environments.
*   Flags like `--build` and `--remove-orphans` are essential for keeping development environments clean and up-to-date.
*   Profiles and multiple compose files (`-f`) allow for flexible, scalable configuration management.
