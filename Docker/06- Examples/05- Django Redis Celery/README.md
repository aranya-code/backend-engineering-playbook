# Django + Redis + Celery

## Overview

This project demonstrates how to build a multi-container Django application using **Docker Compose**, **Redis**, and **Celery**.

Unlike the previous examples, this project introduces **asynchronous background task processing**. Instead of executing long-running operations during an HTTP request, Django sends tasks to Redis, and a dedicated Celery worker processes them independently.

The primary goal is to understand how multiple containers work together—not to learn Django or Celery in depth.

---

# Project Architecture

```text
                    Browser
                        │
                        ▼
                localhost:8000
                        │
                        ▼
               Django Container
                        │
         Docker Compose Network
              │              │
              ▼              ▼
      Redis Container   Celery Worker
              │
              ▼
         Background Queue
```

---

# Docker Concepts Covered

- Docker Compose
- Multi-container applications
- Django in Docker
- Redis Message Broker
- Celery Worker
- Background Tasks
- Environment Variables
- Docker Networking
- Service Discovery
- Health Checks
- Restart Policies

---

# Project Structure

```text
05- Django + Redis + Celery/
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
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   │
│   ├── home/
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── templates/
│   │
│   └── static/
│
├── scripts/
│   ├── start_web.sh
│   └── start_worker.sh
│
└── screenshots/
```

---

# Prerequisites

Before running this project, install:

- Docker Desktop (Windows/macOS)
- Docker Engine + Docker Compose (Linux)
- Basic Docker knowledge

No Redis or Celery experience is required.

---

# Project Files

| File | Purpose |
|------|---------|
| Dockerfile | Builds the Django image |
| compose.yaml | Starts Django, Redis, and Celery |
| config/celery.py | Celery configuration |
| home/tasks.py | Background task definitions |
| start_web.sh | Starts Django with Gunicorn |
| start_worker.sh | Starts the Celery worker |
| .env.example | Sample environment variables |

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
┌────────────┬────────────┐
│            │            │
▼            ▼            ▼
Django     Redis      Celery
```

---

# Background Task Flow

```text
User Clicks Button

        │

        ▼

Django View

        │

        ▼

long_running_task.delay()

        │

        ▼

Redis Queue

        │

        ▼

Celery Worker

        │

        ▼

Background Task

        │

        ▼

Task Completed
```

---

# Quick Start

## 1. Create Environment File

```bash
cp .env.example .env
```

Creates the local configuration file.

---

## 2. Build Images

```bash
docker compose build
```

This command:

- Reads the Dockerfile
- Downloads dependencies
- Builds the Django image
- Reuses cached layers when possible

---

## 3. Start Containers

```bash
docker compose up
```

Docker Compose automatically:

- Creates the Docker network
- Starts Redis
- Performs Redis health checks
- Starts Django
- Starts the Celery Worker

---

## 4. Open the Application

Visit:

```text
http://localhost:8000
```

---

## 5. Trigger a Background Task

Click:

```text
Run Background Task
```

The page immediately reloads.

The task executes inside the Celery Worker.

---

## 6. Stop Everything

```bash
docker compose down
```

---

# Expected Output

## Browser

```text
Django + Redis + Celery

This example demonstrates asynchronous task processing.

[ Run Background Task ]
```

---

## Celery Worker

```text
Starting Celery Worker...

Connected to redis://redis:6379/0

Ready.

============================================================

Task received by Celery Worker.

Processing...

Task completed successfully.

============================================================
```

---

# Docker Compose Services

## web

Responsibilities:

- Serves the Django application
- Accepts browser requests
- Sends background tasks to Redis

---

## redis

Responsibilities:

- Message Broker
- Stores queued tasks
- Connects Django and Celery

---

## worker

Responsibilities:

- Listens for queued tasks
- Executes background jobs
- Runs independently of the web application

---

# Docker Networking

Docker Compose automatically creates an internal network.

Containers communicate using service names.

Instead of:

```text
127.0.0.1
```

Use:

```text
redis
```

Docker automatically resolves the hostname.

---

# Environment Variables

Configuration is loaded from:

```text
.env
```

Example variables:

```text
APP_NAME

SECRET_KEY

DEBUG

CELERY_BROKER
```

Keeping configuration outside the source code makes the project easier to configure across environments.

---

# Health Checks

Redis includes a health check:

```text
redis-cli ping
```

Django and the Celery Worker start only after Redis is healthy.

---

# Useful Commands

Build images

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

View running containers

```bash
docker compose ps
```

View logs

```bash
docker compose logs
```

View Django logs

```bash
docker compose logs web
```

View Celery logs

```bash
docker compose logs worker
```

View Redis logs

```bash
docker compose logs redis
```

Open a shell inside Django

```bash
docker compose exec web bash
```

Open Redis CLI

```bash
docker compose exec redis redis-cli
```

Restart services

```bash
docker compose restart
```

Stop everything

```bash
docker compose down
```

---

# What You Learn

| Docker Concept | Where It Appears |
|----------------|------------------|
| Docker Compose | compose.yaml |
| Multi-Container Applications | Docker Compose |
| Redis Message Broker | redis service |
| Celery Worker | worker service |
| Background Tasks | tasks.py |
| Service Discovery | redis hostname |
| Docker Networking | Compose network |
| Environment Variables | .env |
| Health Checks | Redis service |
| Restart Policies | compose.yaml |

---

# Common Mistakes

## Celery Worker Not Running

The task appears to do nothing.

Solution:

```bash
docker compose logs worker
```

---

## Wrong Redis Host

Incorrect:

```text
localhost
```

Correct:

```text
redis
```

Docker Compose uses service names.

---

## Forgot to Copy `.env`

Without environment variables, Celery cannot connect to Redis.

---

## Redis Not Ready

If Redis is still starting, Django cannot queue tasks.

Docker health checks help avoid this issue.

---

# Best Practices

- Keep web and worker containers separate.
- Use Redis only as a message broker in this example.
- Keep long-running work outside HTTP requests.
- Store configuration in environment variables.
- Use Docker Compose for multi-container applications.
- Keep each container focused on a single responsibility.
- Pin Docker image versions for reproducible builds.

---

# Next Example

The next project introduces **FastAPI + Redis**, demonstrating how Redis can be used as a cache for improving API response times.

---

## Key Takeaways

- Docker Compose simplifies orchestrating multiple cooperating containers.
- Redis acts as a message broker between Django and Celery.
- Celery enables background task processing without blocking web requests.
- Containers communicate through Docker's internal network using service names.
- Separating web requests from background jobs is a common architecture used in production backend systems.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*