# Introduction to Docker Compose

## Overview

Docker Compose is a tool that allows you to define, configure, and run multi-container Docker applications using a single YAML file.

Instead of running multiple `docker run` commands manually, Docker Compose lets you describe your entire application stack in a declarative configuration file.

---

# What is Docker Compose?

## Definition

Docker Compose is a tool for defining and running multi-container Docker applications using a Compose YAML file.

A Compose file describes:

- Services
- Networks
- Volumes
- Environment Variables
- Dependencies

that make up an application.

---

# Why Docker Compose?

Imagine an application with:

```text
Frontend

Backend API

Database
```

Without Compose:

```bash
docker run frontend

docker run backend

docker run mysql
```

Managing multiple containers becomes difficult.

---

# Docker Compose Solution

```text
Compose File

      │

      ▼

docker compose up

      │

      ▼

Application Started
```

All containers start together.

---

# Real-World Example

Web Application

```text
Frontend

Backend

MySQL Database
```

All defined inside one file:

```yaml
services:

  frontend:

  backend:

  mysql:
```

---

# Compose Architecture

```text
docker-compose.yml

        │

        ▼

Docker Compose

        │

        ▼

Containers

Networks

Volumes
```

---

# Compose Workflow

## Step 1

Create a Compose file.

---

## Step 2

Define services.

---

## Step 3

Configure networking.

---

## Step 4

Configure storage.

---

## Step 5

Start application.

```bash
docker compose up
```

---

# Docker Compose vs Docker Run

## Docker Run

```bash
docker run nginx
```

Creates a single container.

---

## Docker Compose

```bash
docker compose up
```

Creates an entire application stack.

---

# Comparison

| Feature | Docker Run | Docker Compose |
|-----------|------------|---------------|
| Single Container | Yes | No |
| Multi-Container | Limited | Yes |
| Infrastructure as Code | No | Yes |
| Easy Reproducibility | Limited | Excellent |
| Production Ready | Limited | Development Focused |

---

# Key Components

## Services

Application containers.

Example:

```yaml
services:

  web:
```

---

## Networks

Container communication.

Example:

```yaml
networks:

  app-network:
```

---

## Volumes

Persistent storage.

Example:

```yaml
volumes:

  db-data:
```

---

## Environment Variables

Configuration values.

Example:

```yaml
environment:

  DB_HOST=mysql
```

---

## Dependencies

Control startup order.

Example:

```yaml
depends_on:

  - mysql
```

---

# Compose File

Default filename:

```text
compose.yaml
```

or

```text
docker-compose.yml
```

Example:

```yaml
services:

  nginx:

    image: nginx
```

---

# Benefits of Docker Compose

## Simplicity

Single command deployment.

---

## Infrastructure as Code

Application configuration stored in version control.

---

## Reproducibility

Consistent environments across machines.

---

## Easy Collaboration

Developers use the same configuration.

---

## Faster Development

Quick startup and teardown.

---

# Typical Use Cases

## Local Development

Most common use case.

---

## Testing Environments

Run complete application stacks.

---

## CI/CD Pipelines

Temporary environments.

---

## Learning Docker

Excellent for understanding containerized applications.

---

# Limitations

## Single Host

Compose runs on one Docker host.

---

## No Native High Availability

Unlike Docker Swarm.

---

## Limited Production Features

No built-in:

```text
Raft

Routing Mesh

Multi-Node Scheduling
```

---

# Docker Compose Lifecycle

```text
Create Compose File

        │

        ▼

docker compose up

        │

        ▼

Containers Running

        │

        ▼

docker compose down

        │

        ▼

Containers Removed
```

---

# Common Commands

## Start Application

```bash
docker compose up
```

---

## Start in Background

```bash
docker compose up -d
```

---

## Stop Application

```bash
docker compose down
```

---

## View Running Containers

```bash
docker compose ps
```

---

## View Logs

```bash
docker compose logs
```

---

# Docker Compose vs Docker Swarm

## Docker Compose

```text
Single Host

Development

Testing
```

---

## Docker Swarm

```text
Multi-Node

Production

High Availability
```

---

# Common Interview Questions

## What is Docker Compose?

Docker Compose is a tool used to define and run multi-container Docker applications using a YAML configuration file.

---

## Why Use Docker Compose?

To simplify management of multi-container applications and make deployments reproducible.

---

## Which File Does Docker Compose Use?

```text
compose.yaml
```

or

```text
docker-compose.yml
```

---

## Which Command Starts a Compose Application?

```bash
docker compose up
```

---

## Which Command Stops a Compose Application?

```bash
docker compose down
```

---

## Is Docker Compose Used for Production?

Primarily for development and testing. Docker Swarm or Kubernetes are more common for production orchestration.

---

# Interview One-Liner

Docker Compose is a tool that uses a YAML configuration file to define and run multi-container Docker applications, enabling developers to deploy complete application environments with a single command.
