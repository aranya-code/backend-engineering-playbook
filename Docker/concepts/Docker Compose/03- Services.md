# Services in Docker Compose

## Overview

Services are the most important component of a Docker Compose file.

A service defines how a container should be created and run.

Every application component in Docker Compose is usually represented as a service.

Examples:

```text
Frontend

Backend

Database

Redis

Nginx
```

---

# What is a Service?

## Definition

A service is a configuration that defines a container, including:

- Image
- Ports
- Volumes
- Networks
- Environment Variables
- Commands

Docker Compose uses this configuration to create containers.

---

# Service Architecture

```text
Compose File

      │

      ▼

Service Definition

      │

      ▼

Container
```

---

# Basic Service Example

```yaml
services:

  web:

    image: nginx
```

Here:

```text
web
```

is the service name.

---

# Service Name

Example:

```yaml
services:

  frontend:

    image: nginx
```

Service name:

```text
frontend
```

---

# Why Service Names Matter

Docker Compose automatically creates DNS entries.

Example:

```text
frontend

backend

database
```

Containers can communicate using service names.

---

# Multiple Services

Example:

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

# Multi-Tier Architecture

```text
Frontend

     │

     ▼

Backend

     │

     ▼

Database
```

Each layer is a service.

---

# Image Directive

Specifies which image to use.

Example:

```yaml
services:

  web:

    image: nginx
```

---

# Versioned Images

Recommended:

```yaml
image: nginx:1.27
```

Avoid:

```yaml
image: nginx:latest
```

for production consistency.

---

# Container Name

Assign custom name.

Example:

```yaml
services:

  web:

    container_name: web-container
```

---

# Ports

Expose container ports.

Example:

```yaml
services:

  web:

    ports:

      - "8080:80"
```

Meaning:

```text
Host Port 8080

Container Port 80
```

---

# Multiple Ports

```yaml
ports:

  - "80:80"

  - "443:443"
```

---

# Environment Variables

Pass configuration into containers.

Example:

```yaml
environment:

  DB_HOST: mysql

  DB_PORT: 3306
```

---

# Alternative Syntax

```yaml
environment:

  - DB_HOST=mysql

  - DB_PORT=3306
```

---

# Volumes

Persist data.

Example:

```yaml
services:

  mysql:

    volumes:

      - db-data:/var/lib/mysql
```

---

# Volume Architecture

```text
Volume

   │

   ▼

Container
```

Data survives container removal.

---

# Bind Mount Example

```yaml
services:

  web:

    volumes:

      - ./app:/app
```

---

# Networks

Connect services together.

Example:

```yaml
services:

  frontend:

    networks:

      - app-network
```

---

# Multiple Networks

```yaml
networks:

  frontend-network

  backend-network
```

Attach:

```yaml
services:

  api:

    networks:

      - frontend-network

      - backend-network
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

# Startup Workflow

```text
MySQL

   │

   ▼

Application
```

---

# Restart Policies

Automatically restart containers.

Example:

```yaml
restart: always
```

---

# Available Options

```text
no

always

on-failure

unless-stopped
```

---

# Command Directive

Override image command.

Example:

```yaml
services:

  app:

    command: python app.py
```

---

# Entrypoint Directive

Override image entrypoint.

Example:

```yaml
services:

  app:

    entrypoint: ["python"]
```

---

# Working Directory

Specify startup directory.

Example:

```yaml
working_dir: /app
```

---

# User Directive

Run container as specific user.

Example:

```yaml
user: "1000:1000"
```

---

# Health Checks

Monitor container health.

Example:

```yaml
healthcheck:

  test: ["CMD", "curl", "-f", "http://localhost"]

  interval: 30s

  timeout: 10s

  retries: 3
```

---

# Build Services

Build image locally.

Example:

```yaml
services:

  web:

    build: .
```

---

# Custom Dockerfile

```yaml
build:

  context: .

  dockerfile: Dockerfile.prod
```

---

# Service Logs

View logs:

```bash
docker compose logs
```

Single service:

```bash
docker compose logs web
```

---

# Service Status

View running services:

```bash
docker compose ps
```

---

# Scaling Services

Example:

```bash
docker compose up --scale web=3
```

Result:

```text
Web 1

Web 2

Web 3
```

---

# Complete Service Example

```yaml
services:

  web:

    image: nginx:1.27

    container_name: web-container

    ports:

      - "8080:80"

    environment:

      APP_ENV: production

    volumes:

      - ./app:/app

    restart: always

    depends_on:

      - mysql
```

---

# Service Lifecycle

```text
Compose File

      │

      ▼

Service Definition

      │

      ▼

Container Creation

      │

      ▼

Container Running
```

---

# Best Practices

## Use Meaningful Names

Example:

```text
frontend

backend

database
```

---

## Use Versioned Images

Avoid:

```yaml
latest
```

---

## Use Health Checks

Monitor service health.

---

## Use Restart Policies

Improve reliability.

---

## Keep Services Independent

Avoid unnecessary coupling.

---

# Common Interview Questions

## What is a Service in Docker Compose?

A service is a configuration that defines how a container should be created and run.

---

## Which Section Defines Services?

```yaml
services:
```

---

## Can Multiple Services Communicate?

Yes.

Docker Compose provides built-in networking and DNS.

---

## Which Directive Exposes Ports?

```yaml
ports:
```

---

## Which Directive Controls Startup Order?

```yaml
depends_on:
```

---

## Which Directive Mounts Storage?

```yaml
volumes:
```

---

## Which Directive Passes Variables?

```yaml
environment:
```

---

# Interview One-Liner

A Docker Compose service is a declarative definition of a container that specifies its image, networking, storage, environment variables, startup behavior, and runtime configuration.
