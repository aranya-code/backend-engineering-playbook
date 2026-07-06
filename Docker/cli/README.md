# 🐳 Docker — CLI Reference

Quick-reference Docker CLI commands, organized by topic. For the concepts behind these commands, see [`../concepts`](../concepts).

---

## Commands

| Topic | Description |
|-------|-------------|
| [Docker Basics](Docker%20Basics.md) | Version, Docker Hub login/logout, and pruning unused resources or dangling images |
| [Images and Containers](Images%20and%20Containers.md) | Pull images, run containers (interactive/detached), custom names, port mapping, list/start containers |
| [Networking](Networking.md) | List, create, and inspect networks; connect and disconnect containers |
| [Volumes and Bind Mounts](Volumes%20and%20Bind%20Mounts.md) | List, create, remove, and prune volumes; mount named volumes and host bind mounts |
| [Docker Compose](Docker%20Compose.md) | Start services from a Compose file, and stop/remove Compose resources |
| [Dockerfile](Dockerfile.md) | Build an image, plus the Python/Django-specific flags and startup commands used in this project's Dockerfile |
| [Docker Swarm](Docker%20Swarm.md) | Init a cluster, manage nodes and services, overlay networks, deploy/inspect/remove stacks |
| [Docker Secrets](Docker%20Secrets.md) | Create, list, inspect, attach to a service, remove, and read mounted secrets |
| [Docker Health Checks](Docker%20Health%20Checks.md) | Run with a health check, check status, Dockerfile HEALTHCHECK syntax, disabling checks |

---

## 🔗 See Also

- [`../concepts`](../concepts) — the theory behind each of these commands
- [`../troubleshooting`](../troubleshooting) — real issues hit during hands-on practice, with fixes
- [`../README.md`](../README.md) — full Docker knowledge base overview

---

*Part of the [backend-engineering-playbook](../../) knowledge base — Aranya Majumdar*