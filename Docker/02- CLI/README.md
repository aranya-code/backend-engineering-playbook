# Docker CLI

## Overview

A professional command reference for Docker CLI, organized by topic. Each file provides practical commands, flag breakdowns, real-world examples with expected output, common mistakes, and best practices.

This reference is designed for backend engineers who need a reliable daily reference and interview preparation guide. For the concepts behind these commands, see [`../concepts`](../concepts).

---

## Repository Structure

```text
cli/
├── README.md                          # This file — index and learning path
├── 01- Docker Basics.md                # System commands, version, login, cleanup
├── 02- Images and Containers.md        # Core lifecycle — run, exec, stop, rm, logs, inspect
├── 03- Dockerfile.md                   # Build commands, flags, multi-stage builds
├── 04- Volumes and Bind Mounts.md      # Persistent storage, bind mounts, tmpfs
├── 05- Networking.md                   # Network drivers, DNS, container communication
├── 06- Docker Compose.md               # Multi-container orchestration with Compose
├── 07- Docker Health Checks.md         # Container health monitoring and debugging
├── 08- Docker Secrets.md               # Secret management for Swarm services
└── 09- Docker Swarm.md                 # Cluster orchestration, services, stacks
```

---


## File Navigation

| # | File | Description |
|---|------|-------------|
| 1 | [Docker Basics](01-%20Docker%20Basics.md) | Version info, Docker Hub login/logout, system cleanup, disk usage |
| 2 | [Images and Containers](02-%20Images%20and%20Containers.md) | Pull images, run/stop/restart containers, exec, logs, inspect, copy files, resource stats |
| 3 | [Dockerfile](03-%20Dockerfile.md) | Build images, build flags, multi-stage builds, `.dockerignore`, Python/Django patterns |
| 4 | [Volumes and Bind Mounts](04-%20Volumes%20and%20Bind%20Mounts.md) | Named volumes, bind mounts, tmpfs, `--mount` syntax, backup and restore |
| 5 | [Networking](05-%20Networking.md) | Network drivers, custom networks, DNS resolution, container isolation |
| 6 | [Docker Compose](06-%20Docker%20Compose.md) | Multi-container apps, service lifecycle, logs, exec, profiles |
| 7 | [Docker Health Checks](07-%20Docker%20Health%20Checks.md) | Health check CLI flags, Dockerfile/Compose syntax, debugging unhealthy containers |
| 8 | [Docker Secrets](08-%20Docker%20Secrets.md) | Secret creation, service attachment, rotation, Compose secrets |
| 9 | [Docker Swarm](09-%20Docker%20Swarm.md) | Cluster init, services, stacks, scaling, rolling updates, node management |

---

## Topics Covered

| Category | Commands Covered |
|----------|-----------------|
| **System** | `docker version`, `docker info`, `docker system prune`, `docker system df`, `docker login` |
| **Images** | `docker pull`, `docker images`, `docker rmi`, `docker tag`, `docker push`, `docker build`, `docker history`, `docker save`, `docker load` |
| **Containers** | `docker run`, `docker exec`, `docker start`, `docker stop`, `docker restart`, `docker kill`, `docker rm`, `docker ps`, `docker logs`, `docker inspect`, `docker cp`, `docker stats`, `docker top`, `docker diff` |
| **Networking** | `docker network create`, `docker network ls`, `docker network connect`, `docker network inspect`, `docker network rm` |
| **Volumes** | `docker volume create`, `docker volume ls`, `docker volume inspect`, `docker volume rm`, `docker volume prune` |
| **Compose** | `docker compose up`, `docker compose down`, `docker compose ps`, `docker compose logs`, `docker compose exec`, `docker compose build`, `docker compose config` |
| **Swarm** | `docker swarm init`, `docker service create`, `docker service scale`, `docker stack deploy`, `docker node ls` |
| **Secrets** | `docker secret create`, `docker secret ls`, `docker secret inspect`, `docker secret rm` |
| **Health** | `--health-cmd`, `--health-interval`, `HEALTHCHECK`, `docker inspect` health output |

---

## Learning Path

### Recommended Learning Order

Follow this sequence to build Docker CLI knowledge progressively:

```text
1. Docker Basics          → System commands, authentication, cleanup
2. Images and Containers  → Core workflow — pull, run, exec, stop, rm
3. Dockerfile             → Building custom images
4. Volumes and Bind Mounts → Persistent and shared storage
5. Networking             → Container communication
6. Docker Compose         → Multi-container applications
7. Docker Health Checks   → Monitoring container health
8. Docker Secrets         → Managing sensitive data
9. Docker Swarm           → Production cluster orchestration
```

> **Tip:** Files 1–6 cover daily development needs. Files 7–9 are relevant for production deployments and interview preparation.

---


## Quick Reference — Comparison Tables

These comparison tables are covered in detail within their respective files:

| Comparison | File |
|------------|------|
| `docker run` vs `docker start` | [Images and Containers](02-%20Images%20and%20Containers.md) |
| `docker exec` vs `docker attach` | [Images and Containers](02-%20Images%20and%20Containers.md) |
| `docker stop` vs `docker kill` | [Images and Containers](02-%20Images%20and%20Containers.md) |
| `docker rm` vs `docker rmi` | [Images and Containers](02-%20Images%20and%20Containers.md) |
| `docker build` vs `docker pull` | [Dockerfile](03-%20Dockerfile.md) |
| `docker compose up` vs `docker compose start` | [Docker Compose](06-%20Docker%20Compose.md) |
| `docker compose down` vs `docker compose stop` | [Docker Compose](06-%20Docker%20Compose.md) |
| Named Volume vs Bind Mount vs tmpfs | [Volumes and Bind Mounts](04-%20Volumes%20and%20Bind%20Mounts.md) |
| Network drivers (bridge, host, overlay, none) | [Networking](05-%20Networking.md) |

---

## Additional Resources

- [Docker CLI Official Reference](https://docs.docker.com/reference/cli/docker/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Docker Compose File Reference](https://docs.docker.com/reference/compose-file/)
- [Docker Hub](https://hub.docker.com/)
- [`../concepts`](../concepts) — Conceptual explanations behind each command
- [`../troubleshooting`](../troubleshooting) — Real issues encountered during practice, with fixes
- [`../README.md`](../README.md) — Full Docker knowledge base overview

---

## Key Takeaways

- This CLI reference covers **9 topic areas** with practical commands, flags, and expected output.
- Every file follows a consistent structure: Overview → Commands → Examples → Mistakes → Best Practices → Key Takeaways.
- Start with **Docker Basics** and **Images and Containers** — these cover 80% of daily Docker usage.
- Comparison tables clarify commonly confused command pairs.
- The reference is designed for both **daily development** and **interview preparation**.

---

*Part of the [backend-engineering-playbook](../../) knowledge base — Aranya Majumdar*