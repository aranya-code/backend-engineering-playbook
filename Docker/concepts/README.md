# 🐳 Docker — Concepts

In-depth conceptual notes on Docker — from fundamentals through Compose, Swarm, and Stacks — plus a production-grade reference Dockerfile. For command syntax, see [`../cli`](../cli); for real issues hit during hands-on practice, see [`../troubleshooting`](../troubleshooting).

---

## 🧱 Core Concepts

| Topic | Description |
|-------|-------------|
| [Docker Basics](Docker-Basics.md) | What Docker is, key benefits, Docker vs VMs, terminology, and workflow |
| [ENTRYPOINT vs CMD](ENTRYPOINT-vs-CMD.md) | Detailed comparison, runtime behavior, override mechanics, and best practices |
| [Shell Form vs Exec Form](Shell-vs-Exec-Form.md) | Signal handling, PID 1 behavior, process tree differences, production recommendations |
| [Volumes & Bind Mounts](Volumes-and-BindMounts.md) | Persistence strategies, architecture differences, when to use each |
| [Health Checks](Docker_Healthchecks.md) | Container health states, Dockerfile and Compose configuration, parameters |
| [Secrets](Docker_Secrets.md) | Secure credential management in Swarm, Raft database storage, mount behavior |
| [Routing Mesh](Routing_Mesh.md) | Swarm ingress load balancing, IPVS, cross-node traffic routing |

---

## 🧩 Docker Compose (10-part series)

Defining and running multi-container applications from a single declarative YAML file.

| # | Topic |
|---|-------|
| 01 | [Introduction](Docker%20Compose/01-%20Introduction.md) |
| 02 | [Compose File Structure](Docker%20Compose/02-%20Compose%20File%20Structure.md) |
| 03 | [Services](Docker%20Compose/03-%20Services.md) |
| 04 | [Networks](Docker%20Compose/04-%20Networks.md) |
| 05 | [Volumes](Docker%20Compose/05-%20Volumes.md) |
| 06 | [Environment Variables](Docker%20Compose/06-%20Environment%20Variables.md) |
| 07 | [Depends On](Docker%20Compose/07-%20Depends%20On.md) |
| 08 | [Profiles](Docker%20Compose/08-%20Profiles.md) |
| 09 | [Commands Cheat Sheet](Docker%20Compose/09-%20Commands%20Cheat%20Sheet.md) |
| 10 | [Interview Questions](Docker%20Compose/10-%20Interview%20Questions.md) |

---

## 🐝 Docker Swarm (13-part series)

Docker's native orchestration and clustering solution for running multiple hosts as one logical cluster.

| # | Topic |
|---|-------|
| 01 | [Introduction](Docker%20Swarm/01-%20Introduction.md) |
| 02 | [Swarm Architecture](Docker%20Swarm/02-%20Swarm%20Architecture.md) |
| 03 | [Manager and Worker Nodes](Docker%20Swarm/03-%20Manager%20and%20Worker%20Nodes.md) |
| 04 | [Swarm Initialization and Cluster Management](Docker%20Swarm/04-%20Swarm%20Initialization%20and%20Cluster%20Management.md) |
| 05 | [Services and Tasks](Docker%20Swarm/05-%20Services%20and%20Tasks.md) |
| 06 | [Service Scaling and Replication](Docker%20Swarm/06-%20Service%20Scaling%20and%20Replication.md) |
| 07 | [Routing Mesh and Load Balancing](Docker%20Swarm/07-%20Routing%20Mesh%20and%20Load%20Balancing.md) |
| 08 | [Overlay Networks](Docker%20Swarm/08-%20Overlay%20Networks.md) |
| 09 | [Rolling Updates and Rollbacks](Docker%20Swarm/09-%20Rolling%20Updates%20and%20Rollbacks.md) |
| 10 | [Docker Swarm Secrets](Docker%20Swarm/10-%20Docker%20Swarm%20Secrets.md) |
| 11 | [High Availability and Raft](Docker%20Swarm/11-%20High%20Availability%20and%20Raft.md) |
| 12 | [Swarm Commands Cheat Sheet](Docker%20Swarm/12-%20Swarm%20Commands%20Cheat%20Sheet.md) |
| 13 | [Docker Swarm vs Kubernetes](Docker%20Swarm/13-%20Docker%20Swarm%20vs%20Kubernetes.md) |

---

## 🗂️ Docker Stacks (5-part series)

Deploying and managing multi-service applications on a Swarm cluster via a single declarative config file.

| # | Topic |
|---|-------|
| 01 | [Introduction](Docker%20Stacks/01-%20Introduction.md) |
| 02 | [Stack Deploy](Docker%20Stacks/02-%20Stack%20Deploy.md) |
| 03 | [Compose vs Stack](Docker%20Stacks/03-%20Compose%20vs%20Stack.md) |
| 04 | [Production Deployment](Docker%20Stacks/04-%20Production%20Deployment.md) |
| 05 | [Interview Questions](Docker%20Stacks/05-%20Interview%20Questions.md) |

---

## 🐍 Reference Dockerfile

[`Dockerfile`](Dockerfile) — a production-grade Django Dockerfile demonstrating:

- `python:3.12-slim` base image (avoids Alpine C-extension build issues)
- `PYTHONDONTWRITEBYTECODE` / `PYTHONUNBUFFERED` environment flags
- A dedicated non-root user for security
- Layer-cache optimization (dependencies copied before application code)
- `collectstatic` chained into the container's startup command

---

## 🔗 See Also

- [`../cli`](../cli) — quick-reference command sheets for everything above
- [`../troubleshooting`](../troubleshooting) — real problems hit during hands-on practice, with fixes
- [`../README.md`](../README.md) — full Docker knowledge base overview

---

*Part of the [backend-engineering-playbook](../../) knowledge base — Aranya Majumdar*