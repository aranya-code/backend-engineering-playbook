# 🐳 Docker Knowledge Base

A structured personal knowledge base covering Docker from fundamentals to production-grade orchestration. Built as a hands-on study reference with concept deep-dives, CLI cheat sheets, a real-world Dockerfile, and documented troubleshooting war stories.

---

## 📁 Repository Structure

```
Docker/
├── concepts/               # In-depth concept notes
│   ├── Docker-Basics.md
│   ├── Dockerfile          # Production-grade Django Dockerfile
│   ├── ENTRYPOINT-vs-CMD.md
│   ├── Shell-vs-Exec-Form.md
│   ├── Volumes-and-BindMounts.md
│   ├── Docker_Healthchecks.md
│   ├── Docker_Secrets.md
│   ├── Routing_Mesh.md
│   ├── Docker Compose/     # 10-part Compose series
│   ├── Docker Swarm/       # 13-part Swarm series
│   └── Docker Stacks/      # 5-part Stacks series
├── cli/                    # Quick-reference command sheets
│   ├── README.md
│   ├── Docker Basics.md
│   ├── Images and Containers.md
│   ├── Networking.md
│   ├── Volumes and Bind Mounts.md
│   ├── Dockerfile.md
│   ├── Docker Compose.md
│   ├── Docker Swarm.md
│   ├── Docker Secrets.md
│   └── Docker Health Checks.md
├── troubleshooting/
│   ├── 01- Container Cannot Connect to Host PostgreSQL.md
│   ├── 02- DRF Admin CSS Missing in Docker.md
│   ├── 03- Container Exits Immediately After Docker Run.md
│   ├── 04- Compose Volumes Must Be a Mapping Error.md
│   └── 05- Swarm Overlay Network Initialization Failure.md
└── images/                 # Screenshots and diagrams
```

---

## 📚 Topics Covered

### Core Concepts

| Topic | Description |
|-------|-------------|
| [Docker Basics](concepts/Docker-Basics.md) | What Docker is, key benefits, Docker vs VMs, terminology, and workflow |
| [ENTRYPOINT vs CMD](concepts/ENTRYPOINT-vs-CMD.md) | Detailed comparison, runtime behavior, override mechanics, and best practices |
| [Shell Form vs Exec Form](concepts/Shell-vs-Exec-Form.md) | Signal handling, PID 1 behavior, process tree differences, production recommendations |
| [Volumes & Bind Mounts](concepts/Volumes-and-BindMounts.md) | Persistence strategies, architecture differences, when to use each |
| [Health Checks](concepts/Docker_Healthchecks.md) | Container health states, Dockerfile and Compose configuration, parameters |
| [Secrets](concepts/Docker_Secrets.md) | Secure credential management in Swarm, Raft database storage, mount behavior |
| [Routing Mesh](concepts/Routing_Mesh.md) | Swarm ingress load balancing, IPVS, cross-node traffic routing |

---

### Docker Compose (10-part series)

| # | Topic |
|---|-------|
| 01 | [Introduction](concepts/Docker%20Compose/01-%20Introduction.md) |
| 02 | [Compose File Structure](concepts/Docker%20Compose/02-%20Compose%20File%20Structure.md) |
| 03 | [Services](concepts/Docker%20Compose/03-%20Services.md) |
| 04 | [Networks](concepts/Docker%20Compose/04-%20Networks.md) |
| 05 | [Volumes](concepts/Docker%20Compose/05-%20Volumes.md) |
| 06 | [Environment Variables](concepts/Docker%20Compose/06-%20Environment%20Variables.md) |
| 07 | [Depends On](concepts/Docker%20Compose/07-%20Depends%20On.md) |
| 08 | [Profiles](concepts/Docker%20Compose/08-%20Profiles.md) |
| 09 | [Commands Cheat Sheet](concepts/Docker%20Compose/09-%20Commands%20Cheat%20Sheet.md) |
| 10 | [Interview Questions](concepts/Docker%20Compose/10-%20Interview%20Questions.md) |

---

### Docker Swarm (13-part series)

| # | Topic |
|---|-------|
| 01 | [Introduction](concepts/Docker%20Swarm/01-%20Introduction.md) |
| 02 | [Swarm Architecture](concepts/Docker%20Swarm/02-%20Swarm%20Architecture.md) |
| 03 | [Manager and Worker Nodes](concepts/Docker%20Swarm/03-%20Manager%20and%20Worker%20Nodes.md) |
| 04 | [Swarm Initialization and Cluster Management](concepts/Docker%20Swarm/04-%20Swarm%20Initialization%20and%20Cluster%20Management.md) |
| 05 | [Services and Tasks](concepts/Docker%20Swarm/05-%20Services%20and%20Tasks.md) |
| 06 | [Service Scaling and Replication](concepts/Docker%20Swarm/06-%20Service%20Scaling%20and%20Replication.md) |
| 07 | [Routing Mesh and Load Balancing](concepts/Docker%20Swarm/07-%20Routing%20Mesh%20and%20Load%20Balancing.md) |
| 08 | [Overlay Networks](concepts/Docker%20Swarm/08-%20Overlay%20Networks.md) |
| 09 | [Rolling Updates and Rollbacks](concepts/Docker%20Swarm/09-%20Rolling%20Updates%20and%20Rollbacks.md) |
| 10 | [Docker Swarm Secrets](concepts/Docker%20Swarm/10-%20Docker%20Swarm%20Secrets.md) |
| 11 | [High Availability and Raft](concepts/Docker%20Swarm/11-%20High%20Availability%20and%20Raft.md) |
| 12 | [Swarm Commands Cheat Sheet](concepts/Docker%20Swarm/12-%20Swarm%20Commands%20Cheat%20Sheet.md) |
| 13 | [Docker Swarm vs Kubernetes](concepts/Docker%20Swarm/13-%20Docker%20Swarm%20vs%20Kubernetes.md) |

---

### Docker Stacks (5-part series)

| # | Topic |
|---|-------|
| 01 | [Introduction](concepts/Docker%20Stacks/01-%20Introduction.md) |
| 02 | [Stack Deploy](concepts/Docker%20Stacks/02-%20Stack%20Deploy.md) |
| 03 | [Compose vs Stack](concepts/Docker%20Stacks/03-%20Compose%20vs%20Stack.md) |
| 04 | [Production Deployment](concepts/Docker%20Stacks/04-%20Production%20Deployment.md) |
| 05 | [Interview Questions](concepts/Docker%20Stacks/05-%20Interview%20Questions.md) |

---

### CLI Reference

Quick-reference command sheets organized by topic:

- [Docker Basics](cli/Docker%20Basics.md) — version, login, prune
- [Images & Containers](cli/Images%20and%20Containers.md) — pull, run, exec, inspect, stats
- [Networking](cli/Networking.md) — create, connect, inspect networks
- [Volumes & Bind Mounts](cli/Volumes%20and%20Bind%20Mounts.md) — volume create, mount syntax
- [Dockerfile](cli/Dockerfile.md) — build commands, Django-specific env vars
- [Docker Compose](cli/Docker%20Compose.md) — up, down
- [Docker Swarm](cli/Docker%20Swarm.md) — init, service, stack commands
- [Docker Secrets](cli/Docker%20Secrets.md) — create, inspect, mount
- [Docker Health Checks](cli/Docker%20Health%20Checks.md) — run, inspect, Dockerfile syntax

---

### Troubleshooting

Real problems encountered and solved, with screenshots:

| # | Problem | Fix |
|---|---------|-----|
| 1 | [Container cannot connect to host PostgreSQL](troubleshooting/01-%20Container%20Cannot%20Connect%20to%20Host%20PostgreSQL.md) | Use `host.docker.internal` or containerize the DB |
| 2 | [DRF/Admin CSS missing in Docker](troubleshooting/02-%20DRF%20Admin%20CSS%20Missing%20in%20Docker.md) | Run `collectstatic` before `runserver` |
| 3 | [Ubuntu container exits immediately after `docker run -d`](troubleshooting/03-%20Container%20Exits%20Immediately%20After%20Docker%20Run.md) | Use `-it` or `-dit` with a foreground process |
| 4 | [`volumes must be a mapping` error in Compose](troubleshooting/04-%20Compose%20Volumes%20Must%20Be%20a%20Mapping%20Error.md) | Remove hyphens from top-level volume declarations |
| 5 | [Overlay network sandbox initialization failure in Swarm](troubleshooting/05-%20Swarm%20Overlay%20Network%20Initialization%20Failure.md) | Remove service → remove network → recreate network → redeploy |

---

## 🐍 Production Dockerfile

A production-ready `Dockerfile` for Django applications is included at [`concepts/Dockerfile`](concepts/Dockerfile).

**Key practices applied:**

- `python:3.12-slim` base image (avoids Alpine C-extension build issues)
- `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED` environment flags
- Non-root user (`django`) for security
- Layer-cache optimization (requirements copied before application code)
- `--no-cache-dir` pip install to keep image size small
- `collectstatic` chained with server startup command
- `EXPOSE 8000` with a note to swap `runserver` for Gunicorn in production

---

## 🎯 Purpose

This repository is a personal Docker study reference built to:

- Consolidate learning into searchable, structured notes
- Prepare for backend engineering interviews (concept explanations + interview Q&A included)
- Document real-world issues and fixes encountered during hands-on practice

---

*Created by Aranya Majumdar*