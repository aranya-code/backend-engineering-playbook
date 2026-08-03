# Docker Basics

## Overview
Docker Basics cover the fundamental commands for managing the Docker environment on your host machine. These commands are essential for authentication, checking system status, monitoring disk usage, and cleaning up unused resources to maintain a healthy Docker engine.

## Common Commands

| Command | Description |
|---|---|
| `docker` | List all available Docker commands and global options |
| `docker -v` | Display the Docker version |
| `docker version` | Display full version information for both client and server |
| `docker info` | Display system-wide information about the Docker installation |
| `docker login -u <username>` | Log in to a Docker registry |
| `docker logout` | Log out from a Docker registry |
| `docker system df` | Show Docker disk usage (images, containers, volumes, build cache) |
| `docker system prune` | Remove unused data (containers, networks, images, and optionally volumes) |
| `docker image prune` | Remove unused (dangling) images |
| `docker system events` | Get real-time events from the Docker server |
| `docker context ls` | List available Docker contexts (e.g., local, remote engines) |

## Command Breakdown

### `docker system prune`
This command is critical for freeing up disk space by removing unused Docker objects.
- `-a` or `--all`: Remove **all** unused images, not just dangling ones (images without a tag).
- `--volumes`: Also remove unused volumes. Volumes are not removed by default to prevent data loss.
- `-f` or `--force`: Bypass the confirmation prompt (useful in automation/CI scripts).
- `--filter`: Provide filter values (e.g., `until=24h` to remove items older than 24 hours).

## Practical Examples

**Checking Docker disk usage:**
```bash
docker system df
```
```text
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          5         2         1.2GB     800MB (66%)
Containers      3         1         150MB     100MB (66%)
Local Volumes   2         1         500MB     250MB (50%)
Build Cache     10        0         2.5GB     2.5GB
```

**Viewing full Docker version:**
```bash
docker version
```
```text
Client: Docker Engine - Community
 Version:           24.0.5
 API version:       1.43
 Go version:        go1.20.6
 Git commit:        ced0996
 Built:             Fri Jul 21 20:32:30 2023
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          24.0.5
  API version:      1.43 (minimum version 1.12)
  Go version:       go1.20.6
  Git commit:       a61e2b4
  Built:            Fri Jul 21 20:32:30 2023
  OS/Arch:          linux/amd64
  Experimental:     false
```

**Displaying system-wide information (abbreviated):**
```bash
docker info
```
```text
Client:
 Context:    default
 Debug Mode: false

Server:
 Containers: 3
  Running: 1
  Paused: 0
  Stopped: 2
 Images: 5
 Server Version: 24.0.5
 Storage Driver: overlay2
 ...
```

## Real-World Use Cases

- **Disk Management:** Running `docker system prune` regularly prevents your development environment or server from running out of disk space due to accumulated images, stopped containers, and build cache.
- **CI/CD Cleanup:** Automating cleanup with `docker system prune -af` at the end of a CI/CD pipeline ensures runners start with a clean slate and avoid storage exhaustion.
- **Debugging & Monitoring:** Using `docker system events` helps trace issues by showing exactly what the Docker daemon is doing in real-time (e.g., container starts, network attachments).
- **Multi-Environment Management:** Using `docker context ls` helps backend engineers seamlessly switch between local development engines and remote staging or production Docker endpoints.

## Common Mistakes

- **Using `docker system prune -a` carelessly:** This flag removes **all** unused images, not just dangling ones. If you have base images that aren't currently used by a running container, they will be deleted and have to be re-downloaded later, slowing down your builds.
- **Forgetting about volumes:** Running a simple `docker system prune` does **not** clean up unused volumes. You must explicitly pass the `--volumes` flag to clear them out, which is often a source of hidden disk usage.
- **Executing scripts without `-f`:** Using `docker system prune` in an automated script without the `--force` (`-f`) flag will cause the script to hang indefinitely waiting for user confirmation.

## Best Practices

- **Regular Maintenance:** Make `docker system df` and `docker system prune` part of your regular maintenance routine to keep your environment lean.
- **Filter Cleanups:** In production or shared environments, use filters with pruning (e.g., `docker system prune --filter "until=168h"`) to only remove resources that have been unused for a specific period (e.g., 7 days).
- **Verify Before Pruning:** Always run `docker system df` before a system prune to understand exactly what is consuming space and what will be reclaimed.

## Related Topics
- [Images and Containers](02-%20Images%20and%20Containers.md)
- [Docker Compose](06-%20Docker%20Compose.md)
- [Volumes and Bind Mounts](04-%20Volumes%20and%20Bind%20Mounts.md)

## Key Takeaways
- `docker system df` is your best tool for auditing Docker's disk space footprint.
- `docker system prune` cleans up unused resources, but requires explicit flags for volumes (`--volumes`) and all unused images (`-a`).
- Authentication (`login`/`logout`) is essential for interacting with private container registries.
- Use `docker info` and `docker version` to quickly diagnose environment configuration and compatibility issues.
