# Docker Volumes and Bind Mounts

## Overview
Containers are ephemeral by design; any data written to the container's writable layer is lost when the container is removed. To persist data (like databases) or share code between the host and container (like local development), Docker provides mechanisms to mount external storage: Volumes, Bind Mounts, and tmpfs.

## Common Commands

| Command | Description |
|---|---|
| `docker volume ls` | List all Docker volumes. |
| `docker volume create <volume>` | Create a new named volume. |
| `docker volume inspect <volume>` | View detailed information about a volume. |
| `docker volume rm <volume>` | Remove a specific volume. |
| `docker volume prune` | Remove all unused local volumes. |
| `docker run -v <volume>:<container-path>` | Run a container with a named volume. |
| `docker run -v <host-path>:<container-path>` | Run a container with a bind mount. |

## Command Breakdown

### Volume Types Comparison

| Type | Persistence | Docker Manages? | Use Case | Shareable? |
|---|---|---|---|---|
| **Named Volume** | High (Host filesystem, managed by Docker) | Yes (`/var/lib/docker/volumes/`) | Databases, persistent app data. | Yes, easily shared among containers. |
| **Bind Mount** | High (Specific path on host) | No (You manage the host directory) | Local development (hot-reload), sharing config files. | Yes, but relies on host directory structure. |
| **tmpfs** | None (In-memory) | N/A (RAM) | Secrets, temporary high-performance caching. | No, bound to a single container. |

### `--mount` vs `-v`
While `-v` (or `--volume`) is common, `--mount` is the modern, more verbose, and less error-prone syntax recommended for services and standalone containers.

```bash
# Using -v
docker run -v my-volume:/app/data nginx

# Using --mount (preferred)
docker run --mount type=volume,source=my-volume,target=/app/data nginx
```

### Read-Only Mounts
You can protect host data from being modified by the container by mounting it as read-only.

```bash
# Using -v syntax
docker run -v my-volume:/app/data:ro nginx

# Using --mount syntax
docker run --mount type=volume,source=my-volume,target=/app/data,readonly nginx
```

## Practical Examples

### Mount a Postgres Data Volume

```bash
# Create a volume
docker volume create pgdata

# Run Postgres and mount the volume to persist data
docker run -d \
  --name mydb \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  postgres
```

### Bind Mount for Local Development Hot-Reload

```bash
# Mounts the current working directory to /usr/src/app in the container
docker run -d \
  --name dev-server \
  -v $(pwd):/usr/src/app \
  -p 3000:3000 \
  node:alpine npm run dev
```

### Backup a Volume Using a Temporary Container

```bash
# Run a temporary Ubuntu container that mounts 'pgdata' and the host's current directory, then creates a tarball
docker run --rm \
  -v pgdata:/volume-data \
  -v $(pwd):/backup \
  ubuntu tar cvf /backup/pgdata-backup.tar /volume-data
```

### Expected Output for `docker volume ls`

```bash
docker volume ls
```
```text
DRIVER    VOLUME NAME
local     pgdata
local     8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d
```

### Expected Output for `docker volume inspect`

```bash
docker volume inspect pgdata
```
```text
[
    {
        "CreatedAt": "2024-05-20T14:32:00Z",
        "Driver": "local",
        "Labels": {},
        "Mountpoint": "/var/lib/docker/volumes/pgdata/_data",
        "Name": "pgdata",
        "Options": {},
        "Scope": "local"
    }
]
```

## Real-World Use Cases
- **Database Persistence:** Using named volumes to ensure that database records (MySQL, PostgreSQL) survive container restarts and upgrades.
- **Local Development Hot-Reload:** Using bind mounts to inject source code from the host into a container, allowing developers to see code changes immediately without rebuilding the image.
- **Shared Configuration:** Mounting a single read-only configuration file from the host to multiple container instances.

## Common Mistakes
- **Using Bind Mounts in Production:** Bind mounts tie your container to a specific host file system structure, reducing portability and causing issues in clustered environments (like Docker Swarm or Kubernetes).
- **Forgetting Volume Cleanup:** Unused volumes consume disk space. Forgetting to run `docker volume prune` can lead to disk exhaustion.
- **Path Issues on Windows:** When using bind mounts on Windows, file paths need to be properly formatted (e.g., using `//c/path/to/dir` or Docker Desktop's path translation) and can suffer from file permission or performance issues.

## Best Practices
- **Prefer Named Volumes over Bind Mounts:** Let Docker manage the storage location for better portability and security, unless you strictly need host file access.
- **Use `--mount` instead of `-v`:** The `--mount` syntax is clearer and fails predictably if a configuration is wrong, whereas `-v` might silently create a new host directory.
- **Mount Configuration as Read-Only:** If a container only needs to read a config file or secret, always append `:ro` or `readonly` to prevent accidental modifications.

## Related Topics
- [Dockerfile](03-%20Dockerfile.md)
- [Networking](05-%20Networking.md)
- [Images and Containers](02-%20Images%20and%20Containers.md)

## Key Takeaways
- Storage inside a container is ephemeral; use Volumes or Bind Mounts for persistence.
- **Named Volumes** are managed by Docker and are the best choice for persistent application data.
- **Bind Mounts** depend on the host OS file structure and are ideal for local development.
- Use `docker volume prune` to reclaim disk space from orphaned volumes.
