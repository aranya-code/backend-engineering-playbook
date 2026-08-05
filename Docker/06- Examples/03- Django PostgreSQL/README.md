# Django with PostgreSQL

## Overview

This project demonstrates how to containerize a Django application and connect it to a PostgreSQL database using Docker Compose.

Unlike the previous examples that used a single container, this project introduces a real-world multi-container architecture where the web application and database run independently while communicating over Docker's internal network.

The primary goal is to understand Docker Compose, service discovery, persistent storage, and environment variable management—not Django development.

---

# Project Architecture

```text
                Browser
                    │
                    ▼
        localhost:8000
                    │
                    ▼
        Django Container (web)
                    │
     Docker Compose Network
                    │
                    ▼
     PostgreSQL Container (postgres)
                    │
                    ▼
          Docker Volume
```

---

# Docker Concepts Covered

- Docker Compose
- Multi-container applications
- Docker networking
- Service discovery
- Named volumes
- PostgreSQL containers
- Environment variables
- Container startup dependencies

---

# Project Structure

```text
03- Django + PostgreSQL/
│
├── README.md
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .dockerignore
├── .gitignore
├── .env.example
│
├── app/
│   ├── manage.py
│   ├── config/
│   ├── home/
│   └── static/
│
├── scripts/
│   └── wait_for_db.sh
│
└── screenshots/
```

---

# Prerequisites

Before running the project, ensure you have:

- Docker Desktop (Windows/macOS)
- Docker Engine + Docker Compose (Linux)
- Basic Docker knowledge
- Basic Django knowledge (optional)

---

# Project Files

| File | Purpose |
|-------|---------|
| Dockerfile | Builds the Django application image |
| compose.yaml | Defines the Django and PostgreSQL containers |
| requirements.txt | Python dependencies |
| .env.example | Sample environment variables |
| wait_for_db.sh | Waits for PostgreSQL before starting Django |
| app/ | Django project source code |

---

# Multi-Container Workflow

```text
Source Code
      │
      ▼
Dockerfile
      │
      ▼
Docker Image
      │
      ▼
Docker Compose
      │
      ▼
Web Container
      │
Docker Network
      │
      ▼
Database Container
```

---

# Quick Start

## 1. Copy Environment Variables

```bash
cp .env.example .env
```

This creates a local environment configuration file.

---

## 2. Build Images

```bash
docker compose build
```

Docker:

- Reads the Dockerfile
- Builds the Django image
- Installs dependencies
- Caches image layers

---

## 3. Start Containers

```bash
docker compose up
```

Docker Compose will:

- Create a network
- Start PostgreSQL
- Create a Docker volume
- Start Django
- Connect both containers

---

## 4. View the Application

Open:

```text
http://localhost:8000
```

---

## 5. Stop Everything

```bash
docker compose down
```

Containers are removed.

The database volume remains.

---

## 6. Remove Everything

```bash
docker compose down -v
```

This also removes the PostgreSQL volume.

---

# Expected Output

Terminal:

```text
Creating network...

Creating volume...

Starting postgres...

Waiting for PostgreSQL...

Applying migrations...

Starting Django...

Watching for file changes...
```

Browser:

```text
Django Docker Example

🎉 Django is running successfully inside Docker.

Framework        Django

Database         docker_demo

Python Version   3.12

Hostname         5e3b8f....
```

---

# Docker Compose Services

## web

Responsibilities:

- Runs Django
- Serves HTTP requests
- Applies migrations
- Connects to PostgreSQL

---

## postgres

Responsibilities:

- Stores application data
- Persists data using Docker Volumes
- Accepts connections from Django

---

# Docker Networking

Docker Compose automatically creates an internal network.

Instead of using an IP address:

```text
172.18.0.2
```

Django connects using the service name:

```text
postgres
```

Docker automatically resolves the hostname.

---

# Persistent Storage

The PostgreSQL container stores data inside:

```text
postgres_data
```

Even if the container is removed, the database remains.

---

# Environment Variables

The project reads configuration from:

```text
.env
```

Examples:

```text
POSTGRES_DB

POSTGRES_USER

POSTGRES_PASSWORD

POSTGRES_HOST

POSTGRES_PORT
```

This keeps configuration separate from the source code.

---

# Useful Commands

Build project

```bash
docker compose build
```

Start containers

```bash
docker compose up
```

Run in background

```bash
docker compose up -d
```

View logs

```bash
docker compose logs
```

View running containers

```bash
docker compose ps
```

Stop containers

```bash
docker compose down
```

Remove everything

```bash
docker compose down -v
```

Restart services

```bash
docker compose restart
```

---

# What You Learn

| Docker Concept | Where It Appears |
|----------------|------------------|
| Dockerfile | Dockerfile |
| Docker Compose | compose.yaml |
| PostgreSQL Container | compose.yaml |
| Named Volumes | compose.yaml |
| Docker Networking | Compose Services |
| Environment Variables | .env |
| Service Discovery | POSTGRES_HOST=postgres |
| Database Initialization | wait_for_db.sh |

---

# Common Mistakes

### PostgreSQL container not ready

The application starts before PostgreSQL.

Solution:

Use `wait_for_db.sh`.

---

### Wrong database hostname

Incorrect:

```text
localhost
```

Correct:

```text
postgres
```

Docker Compose uses service names.

---

### Forgot to copy `.env`

Without a `.env` file, Django cannot connect to PostgreSQL.

---

### Removed the volume accidentally

Running:

```bash
docker compose down -v
```

Deletes the database volume.

---

# Best Practices

- Store secrets in environment variables.
- Keep one service per container.
- Use named volumes for databases.
- Never hardcode database credentials.
- Keep application and database containers separate.
- Pin Docker image versions.
- Keep Dockerfiles simple and readable.

---

# Next Example

The next project introduces **FastAPI + PostgreSQL**, demonstrating how another popular Python framework can be containerized using the same multi-container architecture.

---

## Key Takeaways

- Docker Compose simplifies managing multi-container applications.
- Django and PostgreSQL run in separate containers while communicating over an internal Docker network.
- Docker Volumes provide persistent database storage independent of container lifecycles.
- Environment variables keep application configuration flexible and secure.
- This example demonstrates the foundation used by many real-world backend applications.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*