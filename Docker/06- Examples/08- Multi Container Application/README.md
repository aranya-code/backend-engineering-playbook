# Multi-Container Application

## Overview

This project combines everything learned in the previous Docker examples into a single multi-container backend application.

Instead of demonstrating one Docker concept, this example shows how multiple services cooperate to build a small backend system.

The application consists of four containers:

- Nginx
- FastAPI
- Redis
- Celery Worker

Each container has a single responsibility and communicates with the others through Docker Compose's internal network.

This architecture closely resembles many real-world backend systems.

---

# Project Architecture

```text
                     Browser
                         │
                         ▼
                 localhost:80
                         │
                         ▼
                Nginx Container
                         │
         Docker Compose Network
                         │
                         ▼
               FastAPI Container
                 │            │
                 │            │
                 ▼            ▼
          Redis Cache    Redis Broker
                 │            │
                 └──────┬─────┘
                        ▼
                Celery Worker
```

---

# Docker Concepts Covered

- Docker Compose
- Multi-container applications
- FastAPI
- Nginx Reverse Proxy
- Redis Cache
- Redis Message Broker
- Celery Worker
- Docker Networking
- Service Discovery
- Environment Variables
- Health Checks
- Restart Policies

---

# Project Structure

```text
08- Multi-Container Application/
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
│   ├── main.py
│   ├── settings.py
│   │
│   ├── routers/
│   │   ├── home.py
│   │   ├── products.py
│   │   └── tasks.py
│   │
│   ├── services/
│   │   ├── cache_service.py
│   │   ├── product_service.py
│   │   └── task_service.py
│   │
│   └── static/
│
├── celery_worker/
│   ├── celery_app.py
│   └── tasks.py
│
├── nginx/
│   ├── nginx.conf
│   └── default.conf
│
├── scripts/
│   ├── start_api.sh
│   └── start_worker.sh
│
└── screenshots/
```

---

# Prerequisites

Before running this project, install:

- Docker Desktop (Windows/macOS)
- Docker Engine + Docker Compose (Linux)

Basic familiarity with Docker containers is recommended.

---

# Project Components

| Component | Responsibility |
|-----------|----------------|
| Nginx | Reverse proxy |
| FastAPI | API server |
| Redis | Cache + Message Broker |
| Celery | Background task processing |

---

# Overall Application Flow

```text
Browser

    │

    ▼

Nginx

    │

    ▼

FastAPI

 ┌───────────────┐

 ▼               ▼

Redis Cache   Redis Broker

                  │

                  ▼

            Celery Worker
```

---

# API Endpoints

## Home

```text
GET /
```

Returns

```json
{
    "service": "Multi-Container Demo",
    "status": "running"
}
```

---

## Cached Products

```text
GET /products
```

Demonstrates Redis caching.

---

## Background Task

```text
POST /tasks
```

Queues a Celery task.

---

# Request Flows

## Basic Request

```text
Browser

↓

Nginx

↓

FastAPI

↓

Response
```

---

## Cached Request

```text
Browser

↓

FastAPI

↓

Redis

↓

Cached Response
```

---

## Background Task

```text
Browser

↓

FastAPI

↓

Redis Queue

↓

Celery Worker

↓

Background Processing
```

---

# Quick Start

## 1. Copy Environment Variables

```bash
cp .env.example .env
```

---

## 2. Build Images

```bash
docker compose build
```

Docker will:

- Read the Dockerfile
- Install dependencies
- Build the application image

---

## 3. Start Containers

```bash
docker compose up
```

Docker Compose automatically:

- Creates the Docker network
- Starts Redis
- Performs Redis health checks
- Starts FastAPI
- Starts the Celery worker
- Starts Nginx

---

## 4. Open the Application

```text
http://localhost
```

---

## 5. Test Redis Cache

```text
GET /products
```

First request

```text
Cache Miss
```

Second request

```text
Cache Hit
```

---

## 6. Test Background Tasks

```text
POST /tasks
```

Watch the Celery Worker logs.

---

## 7. Stop Everything

```bash
docker compose down
```

---

# Container Startup

```text
docker compose up

        │

        ▼

Redis Starts

        │

        ▼

Health Check

        │

        ▼

FastAPI Starts

        │

        ▼

Health Check

        │

        ▼

Celery Worker Starts

        │

        ▼

Nginx Starts

        │

        ▼

Application Ready
```

---

# Docker Networking

Docker Compose creates a private network.

Container communication:

```text
Nginx

↓

api

↓

redis

↓

worker
```

Service names are used instead of IP addresses.

---

# Redis Responsibilities

Redis performs two different jobs.

## Cache

```text
/products

↓

Redis Cache

↓

Fast Response
```

---

## Message Broker

```text
/tasks

↓

Redis Queue

↓

Celery Worker
```

---

# Environment Variables

Configuration is loaded from:

```text
.env
```

Variables

```text
APP_NAME

REDIS_HOST

REDIS_PORT

CACHE_TTL
```

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

View all logs

```bash
docker compose logs
```

View FastAPI logs

```bash
docker compose logs api
```

View Celery logs

```bash
docker compose logs worker
```

View Redis logs

```bash
docker compose logs redis
```

View Nginx logs

```bash
docker compose logs nginx
```

Open FastAPI shell

```bash
docker compose exec api sh
```

Open Redis CLI

```bash
docker compose exec redis redis-cli
```

List cache keys

```bash
KEYS *
```

Inspect cached products

```bash
GET products
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

| Concept | Where It Appears |
|----------|------------------|
| Docker Compose | compose.yaml |
| Reverse Proxy | Nginx |
| FastAPI | API Service |
| Redis Cache | Product Endpoint |
| Redis Broker | Celery |
| Background Tasks | `/tasks` |
| Docker Networking | Internal Network |
| Service Discovery | Docker DNS |
| Health Checks | compose.yaml |
| Restart Policies | compose.yaml |

---

# Common Mistakes

## Using localhost Between Containers

Incorrect

```text
localhost
```

Correct

```text
redis

api
```

Docker Compose uses service names.

---

## Exposing Internal Services

Only Nginx should publish ports.

FastAPI, Redis, and Celery remain internal.

---

## Confusing Redis Cache and Broker

Redis serves two separate purposes:

- Cache
- Message Broker

The same Redis instance is used for both in this learning example.

---

## Celery Worker Not Running

If tasks never execute:

```bash
docker compose logs worker
```

---

# Best Practices

- One responsibility per container.
- Expose only the reverse proxy.
- Use Docker service names for communication.
- Keep long-running work outside HTTP requests.
- Cache expensive operations.
- Add health checks to critical services.
- Keep configuration in environment variables.
- Pin image versions for reproducible builds.

---

# Key Takeaways

- Docker Compose makes it easy to orchestrate multiple cooperating containers.
- Nginx acts as the public entry point while FastAPI remains internal.
- Redis serves both as a cache and a Celery message broker in this example.
- Celery enables asynchronous processing without blocking HTTP requests.
- Separating responsibilities across containers leads to a cleaner and more scalable architecture.
- This example brings together the core concepts introduced throughout the Docker examples into one cohesive application.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*