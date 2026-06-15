# Docker Compose vs Docker Stack

## Overview

Docker Compose and Docker Stack both use YAML files to define multi-container applications, but they serve different purposes.

Docker Compose is primarily designed for local development and testing.

Docker Stack is designed for Docker Swarm production deployments.

---

# What is Docker Compose?

Docker Compose is a tool used to define and run multi-container applications on a single Docker host.

Command:

```bash
docker compose up
```

Typical Use Cases:

- Local Development
- Testing
- Lab Environments
- CI/CD Testing

---

# What is Docker Stack?

Docker Stack is a Swarm feature used to deploy multi-service applications across multiple nodes.

Command:

```bash
docker stack deploy
```

Typical Use Cases:

- Production Deployments
- Multi-Node Clusters
- High Availability Applications
- Scalable Services

---

# Architecture Comparison

## Docker Compose

```text
Single Host

 ├── Container 1
 ├── Container 2
 └── Container 3
```

---

## Docker Stack

```text
Manager Node

      │

      ▼

Worker 1
Worker 2
Worker 3
```

Services can run across multiple nodes.

---

# Deployment Commands

## Docker Compose

```bash
docker compose up -d
```

---

## Docker Stack

```bash
docker stack deploy -c stack.yml myapp
```

---

# Environment Comparison

| Feature | Docker Compose | Docker Stack |
|-----------|---------------|--------------|
| Single Host | Yes | No |
| Multi-Node | No | Yes |
| Swarm Required | No | Yes |
| Production Ready | Limited | Yes |
| High Availability | No | Yes |

---

# Networking

## Docker Compose

Creates:

```text
Bridge Network
```

Communication occurs only on a single host.

---

## Docker Stack

Creates:

```text
Overlay Network
```

Communication works across multiple swarm nodes.

---

# Scaling

## Docker Compose

Scale manually:

```bash
docker compose up --scale web=3
```

Limited functionality.

---

## Docker Stack

Native scaling:

```bash
docker service scale web=10
```

Fully integrated with Swarm.

---

# High Availability

## Docker Compose

```text
No High Availability
```

If host fails:

```text
Application Down
```

---

## Docker Stack

Uses:

```text
Manager Nodes

Worker Nodes

Raft Consensus
```

Supports failover and recovery.

---

# Load Balancing

## Docker Compose

No built-in load balancing.

---

## Docker Stack

Built-in:

```text
Routing Mesh
```

Traffic distributed automatically.

---

# Rolling Updates

## Docker Compose

No native rolling update mechanism.

---

## Docker Stack

Supports:

```text
Rolling Updates

Rollbacks
```

through Docker Swarm.

---

# Secrets

## Docker Compose

Can use environment variables.

Limited secret management.

---

## Docker Stack

Uses:

```bash
docker secret create
```

Encrypted secret storage.

---

# Configurations

## Docker Compose

Basic configuration management.

---

## Docker Stack

Supports:

```text
Configs

Secrets

Deployment Policies
```

---

# Service Discovery

## Docker Compose

DNS works on a single host.

---

## Docker Stack

Cluster-wide DNS.

Example:

```text
frontend → backend
```

across different nodes.

---

# Resource Management

## Docker Compose

Limited production controls.

---

## Docker Stack

Supports:

```yaml
deploy:

  resources:

    limits:

      cpus: "1.0"

      memory: 512M
```

---

# Example Compose File

```yaml
version: "3.9"

services:

  web:
    image: nginx

  api:
    image: httpd
```

Run:

```bash
docker compose up -d
```

---

# Example Stack File

```yaml
version: "3.9"

services:

  web:
    image: nginx

    deploy:
      replicas: 3
```

Deploy:

```bash
docker stack deploy -c stack.yml myapp
```

---

# Production Considerations

Use Docker Compose when:

```text
Developing Applications

Testing Locally

Learning Docker
```

---

Use Docker Stack when:

```text
Running Production Workloads

Need High Availability

Need Multi-Node Deployment

Need Rolling Updates
```

---

# Detailed Comparison Table

| Feature | Docker Compose | Docker Stack |
|-----------|---------------|--------------|
| Deployment Command | docker compose up | docker stack deploy |
| Host Type | Single Host | Swarm Cluster |
| Networking | Bridge | Overlay |
| Scaling | Limited | Native |
| High Availability | No | Yes |
| Routing Mesh | No | Yes |
| Rolling Updates | No | Yes |
| Rollbacks | No | Yes |
| Secrets | Limited | Full Support |
| Production Usage | Limited | Recommended |

---

# Migration Path

Common progression:

```text
Docker Run

      ▼

Docker Compose

      ▼

Docker Swarm + Stack

      ▼

Kubernetes
```

---

# Common Interview Questions

## What is the Difference Between Compose and Stack?

Docker Compose manages containers on a single host, while Docker Stack deploys services across a Docker Swarm cluster.

---

## Which Command Deploys a Stack?

```bash
docker stack deploy
```

---

## Does Docker Stack Require Swarm?

Yes.

Swarm mode must be enabled.

---

## Which Supports High Availability?

Docker Stack.

---

## Which Uses Overlay Networks?

Docker Stack.

---

## Which Supports Rolling Updates?

Docker Stack.

---

# Interview One-Liner

Docker Compose is designed for defining and running multi-container applications on a single Docker host, while Docker Stack uses the same Compose-based approach to deploy scalable, highly available applications across a Docker Swarm cluster.
