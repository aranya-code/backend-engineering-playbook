# Compose File Structure

## Overview

The Compose file is the heart of Docker Compose.

It defines:

- Services
- Networks
- Volumes
- Environment Variables
- Dependencies
- Configurations

required to run an application.

Docker Compose reads this file and automatically creates the required containers and resources.

---

# Default File Names

Docker Compose automatically looks for:

```text
compose.yaml
```

or

```text
docker-compose.yml
```

---

# Basic Structure

Example:

```yaml
services:

  web:

    image: nginx
```

This is the smallest valid Compose file.

---

# Complete Structure

```yaml
services:

networks:

volumes:

configs:

secrets:
```

Not all sections are mandatory.

---

# YAML Basics

Compose files use YAML syntax.

Example:

```yaml
services:

  web:

    image: nginx
```

Important:

```text
Indentation Matters
```

Use spaces, not tabs.

---

# Service Section

## Definition

The service section defines application containers.

Example:

```yaml
services:

  web:

    image: nginx

  api:

    image: httpd
```

---

# Service Name

```yaml
services:

  frontend:
```

Here:

```text
frontend
```

is the service name.

---

# Image

Specify container image.

Example:

```yaml
services:

  web:

    image: nginx
```

---

# Container Name

Example:

```yaml
services:

  web:

    container_name: nginx-container
```

---

# Ports

Map host ports to container ports.

Example:

```yaml
services:

  web:

    ports:

      - "8080:80"
```

Meaning:

```text
Host 8080

Container 80
```

---

# Environment Variables

Example:

```yaml
services:

  app:

    environment:

      DB_HOST: mysql

      DB_PORT: 3306
```

---

# Volumes

Mount persistent storage.

Example:

```yaml
services:

  mysql:

    volumes:

      - db-data:/var/lib/mysql
```

---

# Networks

Attach services to networks.

Example:

```yaml
services:

  frontend:

    networks:

      - app-network
```

---

# Depends On

Control startup order.

Example:

```yaml
services:

  app:

    depends_on:

      - mysql
```

---

# Restart Policies

Example:

```yaml
services:

  web:

    restart: always
```

Options:

```text
no

always

unless-stopped

on-failure
```

---

# Command

Override default container command.

Example:

```yaml
services:

  nginx:

    command: nginx -g "daemon off;"
```

---

# Entrypoint

Override image entrypoint.

Example:

```yaml
services:

  app:

    entrypoint: ["python"]
```

---

# Build Section

Build images from Dockerfiles.

Example:

```yaml
services:

  web:

    build: .
```

---

# Custom Dockerfile

```yaml
services:

  web:

    build:

      context: .

      dockerfile: Dockerfile.prod
```

---

# Networks Section

Define custom networks.

Example:

```yaml
networks:

  app-network:
```

---

# Multiple Networks

```yaml
networks:

  frontend-network:

  backend-network:
```

---

# Volumes Section

Define named volumes.

Example:

```yaml
volumes:

  db-data:
```

---

# Named Volume Architecture

```text
Volume

   │

   ▼

Container
```

Data survives container deletion.

---

# Secrets Section

Example:

```yaml
secrets:

  db_password:
```

Mostly used with Docker Swarm.

---

# Configs Section

Example:

```yaml
configs:

  nginx-config:
```

Primarily used in Swarm deployments.

---

# Multi-Service Example

```yaml
services:

  frontend:

    image: nginx

  backend:

    image: httpd

  database:

    image: mysql
```

---

# Three-Tier Architecture

```text
Frontend

     │

     ▼

Backend

     │

     ▼

Database
```

Defined within a single Compose file.

---

# Complete Example

```yaml
services:

  web:

    image: nginx

    ports:

      - "8080:80"

    networks:

      - app-network

  mysql:

    image: mysql

    environment:

      MYSQL_ROOT_PASSWORD: password

    volumes:

      - db-data:/var/lib/mysql

networks:

  app-network:

volumes:

  db-data:
```

---

# Validation

Validate Compose file:

```bash
docker compose config
```

---

# Common Structure Errors

## Bad Indentation

Wrong:

```yaml
services:

web:
image: nginx
```

---

Correct:

```yaml
services:

  web:

    image: nginx
```

---

# Invalid YAML

Always validate:

```bash
docker compose config
```

before deployment.

---

# Compose File Workflow

```text
Compose File

      │

      ▼

Validation

      │

      ▼

docker compose up

      │

      ▼

Containers Running
```

---

# Best Practices

## Use Meaningful Service Names

Example:

```yaml
frontend

backend

database
```

---

## Use Named Volumes

Avoid data loss.

---

## Use Environment Variables

Avoid hardcoding values.

---

## Validate Before Running

```bash
docker compose config
```

---

## Keep Files Readable

Use proper indentation and organization.

---

# Common Interview Questions

## What is the Main File Used by Docker Compose?

```text
compose.yaml
```

or

```text
docker-compose.yml
```

---

## Which Section Defines Containers?

```yaml
services:
```

---

## Which Section Defines Persistent Storage?

```yaml
volumes:
```

---

## Which Section Defines Networking?

```yaml
networks:
```

---

## Which Command Validates a Compose File?

```bash
docker compose config
```

---

# Interview One-Liner

The Docker Compose file is a YAML-based configuration file that declaratively defines services, networks, volumes, environment variables, and dependencies required to deploy a multi-container application.
