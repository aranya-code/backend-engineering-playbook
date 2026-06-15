# Production Deployment with Docker Stacks

## Overview

Docker Stacks become truly powerful in production environments where applications require:

- High Availability
- Scalability
- Fault Tolerance
- Secure Configuration
- Resource Management
- Automated Updates

This file focuses on production-ready deployment patterns using Docker Stacks and Docker Swarm.

---

# Production Architecture

Typical Production Stack:

```text
Frontend Service

Backend Service

Database Service

Cache Service

Overlay Network

Volumes

Secrets

Configs
```

All deployed using a single stack file.

---

# Production Stack Structure

```yaml
version: "3.9"

services:

  frontend:

  backend:

  database:

networks:

volumes:

secrets:

configs:
```

---

# Deploy Section

The deploy section contains Swarm-specific production settings.

Example:

```yaml
deploy:

  replicas: 3
```

---

# Service Replicas

Run multiple copies of an application.

Example:

```yaml
services:

  frontend:

    image: nginx

    deploy:

      replicas: 3
```

Result:

```text
Frontend Replica 1

Frontend Replica 2

Frontend Replica 3
```

---

# Why Use Replicas?

Benefits:

- High Availability
- Load Distribution
- Fault Tolerance
- Scalability

---

# Restart Policies

Control container recovery behavior.

Example:

```yaml
deploy:

  restart_policy:

    condition: any
```

---

# Available Options

```text
none

on-failure

any
```

---

# Example

```yaml
restart_policy:

  condition: on-failure
```

Container restarts only after failures.

---

# Placement Constraints

Control where services run.

---

## Run Only on Workers

```yaml
deploy:

  placement:

    constraints:

      - node.role == worker
```

---

## Run Only on Managers

```yaml
deploy:

  placement:

    constraints:

      - node.role == manager
```

---

# Resource Limits

Prevent containers from consuming excessive resources.

---

## CPU Limit

```yaml
deploy:

  resources:

    limits:

      cpus: "1.0"
```

---

## Memory Limit

```yaml
deploy:

  resources:

    limits:

      memory: 512M
```

---

# Complete Example

```yaml
deploy:

  resources:

    limits:

      cpus: "1.0"

      memory: 512M
```

---

# Resource Reservations

Reserve resources for critical workloads.

```yaml
deploy:

  resources:

    reservations:

      cpus: "0.25"

      memory: 128M
```

---

# Rolling Updates

Update applications without downtime.

Example:

```yaml
deploy:

  update_config:

    parallelism: 1

    delay: 10s
```

---

# Update Workflow

```text
Old Container

      ▼

New Container

      ▼

Wait

      ▼

Update Next Container
```

---

# Rollback Configuration

Restore previous versions safely.

```yaml
deploy:

  rollback_config:

    parallelism: 1

    delay: 10s
```

---

# Overlay Networks

Production applications should use overlay networks.

Example:

```yaml
networks:

  app-network:

    driver: overlay
```

---

# Service Communication

```text
Frontend

     │

     ▼

Backend

     │

     ▼

Database
```

Communication occurs through the overlay network.

---

# Volumes

Persistent storage for stateful services.

Example:

```yaml
volumes:

  db-data:
```

---

# Mount Volume

```yaml
services:

  mysql:

    volumes:

      - db-data:/var/lib/mysql
```

---

# Why Use Volumes?

Without volume:

```text
Container Removed

      ▼

Data Lost
```

With volume:

```text
Container Removed

      ▼

Data Preserved
```

---

# Docker Secrets

Store sensitive information securely.

---

## Create Secret

```bash
docker secret create db_password password.txt
```

---

## Use Secret

```yaml
services:

  mysql:

    secrets:

      - db_password
```

---

# Configs

Store application configuration files.

Example:

```yaml
configs:

  nginx-config:
    external: true
```

---

# Attach Config

```yaml
services:

  nginx:

    configs:

      - nginx-config
```

---

# Production Networking

Recommended:

```text
Frontend Network

Backend Network

Monitoring Network
```

Instead of one large network.

---

# Example Production Stack

```yaml
version: "3.9"

services:

  frontend:

    image: nginx:1.27

    deploy:

      replicas: 3

  backend:

    image: my-api:1.0

    deploy:

      replicas: 2

  database:

    image: mysql:8

    volumes:

      - db-data:/var/lib/mysql

networks:

  app-network:

    driver: overlay

volumes:

  db-data:
```

---

# Deploy Production Stack

```bash
docker stack deploy -c production.yml production
```

---

# Update Production Stack

Modify:

```yaml
image: nginx:1.28
```

Redeploy:

```bash
docker stack deploy -c production.yml production
```

Rolling update occurs automatically.

---

# Monitoring Production Stacks

## View Stacks

```bash
docker stack ls
```

---

## View Services

```bash
docker stack services production
```

---

## View Tasks

```bash
docker stack ps production
```

---

## View Logs

```bash
docker service logs <service>
```

---

# Production Best Practices

## Use Multiple Replicas

```yaml
replicas: 3
```

or more.

---

## Use Resource Limits

Protect cluster resources.

---

## Use Secrets

Avoid:

```yaml
MYSQL_PASSWORD=password123
```

---

## Use Overlay Networks

Enable secure service communication.

---

## Use Rolling Updates

Prevent downtime.

---

## Use Versioned Images

Avoid:

```yaml
image: nginx:latest
```

Prefer:

```yaml
image: nginx:1.27
```

---

## Store Stack Files in Git

Infrastructure as Code.

---

# Common Production Challenges

## Service Fails to Start

Check:

```bash
docker stack ps production
```

---

## Image Pull Failure

Verify:

```text
Image Name

Registry Access

Credentials
```

---

## Network Issues

Inspect:

```bash
docker network inspect
```

---

## Secret Errors

Verify:

```bash
docker secret ls
```

---

# Common Interview Questions

## Why Use Replicas in Production?

To improve availability, load balancing, and fault tolerance.

---

## Why Use Secrets?

To securely store passwords, API keys, and certificates.

---

## Why Use Resource Limits?

To prevent a single service from consuming excessive cluster resources.

---

## How Are Rolling Updates Configured?

Using:

```yaml
update_config:
```

inside the deploy section.

---

## Why Use Overlay Networks?

To allow services running on different swarm nodes to communicate securely.

---

# Interview One-Liner

Production Docker Stack deployments use replicas, resource limits, placement constraints, secrets, configs, overlay networks, rolling updates, and persistent volumes to deliver highly available, scalable, and fault-tolerant applications on Docker Swarm.
