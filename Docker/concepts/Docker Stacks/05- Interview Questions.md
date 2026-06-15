# Docker Stack Interview Questions

## Overview

This file contains the most commonly asked Docker Stack interview questions, ranging from beginner to advanced levels.

Use this as a final revision guide before interviews and certifications.

---

# Beginner Questions

## What is a Docker Stack?

A Docker Stack is a collection of services deployed and managed together in a Docker Swarm cluster using a Compose file.

---

## Why Do We Use Docker Stacks?

Docker Stacks simplify deployment and management of multi-service applications by allowing all services to be defined and deployed together.

---

## Which Command Deploys a Docker Stack?

```bash
docker stack deploy
```

Example:

```bash
docker stack deploy -c stack.yml myapp
```

---

## Which File Format Does Docker Stack Use?

Docker Compose YAML format.

Example:

```yaml
version: "3.9"

services:

  web:

  api:
```

---

## Does Docker Stack Require Docker Swarm?

Yes.

Docker Stack works only when Swarm mode is enabled.

Verify:

```bash
docker info
```

Look for:

```text
Swarm: active
```

---

# Intermediate Questions

## What is the Difference Between Docker Compose and Docker Stack?

Docker Compose is designed for a single Docker host, while Docker Stack deploys applications across a Docker Swarm cluster.

---

## Which Command Lists All Stacks?

```bash
docker stack ls
```

---

## Which Command Shows Services Inside a Stack?

```bash
docker stack services <stack-name>
```

Example:

```bash
docker stack services myapp
```

---

## Which Command Displays Tasks Running in a Stack?

```bash
docker stack ps <stack-name>
```

---

## Which Command Removes a Stack?

```bash
docker stack rm <stack-name>
```

---

# Production Questions

## Can Docker Stacks Scale Applications?

Yes.

Using replicas:

```yaml
deploy:

  replicas: 3
```

or:

```bash
docker service scale
```

---

## Do Docker Stacks Support Rolling Updates?

Yes.

Example:

```yaml
update_config:

  parallelism: 1

  delay: 10s
```

---

## Do Docker Stacks Support Rollbacks?

Yes.

Example:

```yaml
rollback_config:

  parallelism: 1
```

---

## Can Docker Stacks Use Overlay Networks?

Yes.

Example:

```yaml
networks:

  app-network:

    driver: overlay
```

---

## Can Docker Stacks Use Volumes?

Yes.

Example:

```yaml
volumes:

  db-data:
```

---

## Can Docker Stacks Use Docker Secrets?

Yes.

Example:

```yaml
services:

  mysql:

    secrets:

      - db_password
```

---

# Advanced Questions

## What Happens When a Stack is Deployed?

Workflow:

```text
Compose File

      ▼

Stack Deployment

      ▼

Services Created

      ▼

Tasks Scheduled

      ▼

Containers Started
```

---

## What Happens When a Stack File is Updated?

Redeploying the stack causes Docker Swarm to compare the desired state with the current state and perform rolling updates where necessary.

---

## Can a Docker Stack Span Multiple Nodes?

Yes.

Docker Stack is designed for Docker Swarm clusters and can distribute services across multiple nodes.

---

## How Does Service Discovery Work in Docker Stacks?

Services communicate through built-in DNS.

Example:

```text
frontend → backend
```

without requiring hardcoded IP addresses.

---

## How Does High Availability Work?

Docker Swarm maintains service replicas and automatically reschedules failed tasks on healthy nodes.

---

# Scenario-Based Questions

## A Container Fails. What Happens?

Docker Swarm detects the failure and automatically creates a replacement task to maintain the desired state.

---

## A Worker Node Fails. What Happens?

Services running on the failed worker are rescheduled onto healthy nodes if sufficient resources are available.

---

## A Manager Node Fails. What Happens?

If quorum exists, another manager becomes leader through Raft leader election.

---

## How Would You Deploy a Three-Tier Application?

Example:

```text
Frontend

Backend

Database
```

Using:

```yaml
services:

  frontend:

  backend:

  database:
```

inside a stack file.

---

## How Would You Secure Database Passwords?

Using Docker Secrets instead of environment variables.

---

# Comparison Questions

## Docker Stack vs Docker Compose?

Compose:

```text
Single Host
Development
```

Stack:

```text
Docker Swarm
Production
```

---

## Docker Stack vs Kubernetes?

Docker Stack is simpler and easier to learn.

Kubernetes provides a larger ecosystem and more advanced orchestration features.

---

## Docker Stack vs Individual Services?

Stacks allow applications to be managed as a single deployment unit instead of multiple independent services.

---

# Rapid-Fire Questions

## Deploy a Stack

```bash
docker stack deploy
```

---

## List Stacks

```bash
docker stack ls
```

---

## View Stack Services

```bash
docker stack services
```

---

## View Stack Tasks

```bash
docker stack ps
```

---

## Remove Stack

```bash
docker stack rm
```

---

## Scale Service

```bash
docker service scale
```

---

## Create Secret

```bash
docker secret create
```

---

## View Nodes

```bash
docker node ls
```

---

# Top 10 Most Asked Interview Questions

1. What is Docker Stack?
2. How is Docker Stack different from Docker Compose?
3. Which command deploys a stack?
4. Does Docker Stack require Swarm?
5. Can Docker Stacks scale services?
6. How do rolling updates work?
7. Can Docker Stacks use Secrets?
8. Can Docker Stacks use Overlay Networks?
9. How does service discovery work?
10. What happens when a node fails?

---

# One-Line Revision Answers

## Docker Stack

A collection of services deployed together in Docker Swarm.

---

## Deployment Command

```bash
docker stack deploy
```

---

## Scaling

```yaml
deploy:
  replicas: N
```

---

## Networking

Overlay Networks.

---

## Secrets

Docker Secrets.

---

## High Availability

Docker Swarm + Raft.

---

## Service Discovery

Built-in DNS.

---

## Rolling Updates

```yaml
update_config
```

---

## Rollbacks

```yaml
rollback_config
```

---

## Remove Stack

```bash
docker stack rm
```

---

# Final Interview One-Liner

Docker Stacks provide a declarative, production-ready deployment model for Docker Swarm, allowing multi-service applications to be deployed, scaled, updated, secured, and managed as a single unit using Compose-based configuration files.
