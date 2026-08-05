# FastAPI - Redis

## Overview

This project demonstrates how to use **Redis as a cache** for a FastAPI application running inside Docker.

Unlike the previous example where Redis was used as a **message broker** for Celery, this project focuses entirely on **response caching**.

The application simulates an expensive operation by waiting for five seconds before returning data. The first request stores the response in Redis, and subsequent requests are served directly from the cache, resulting in significantly faster response times.

The goal of this project is to understand Docker Compose, Redis caching, cache hits, cache misses, and multi-container communication.

---

# Project Architecture

```text
                    Client
                       │
                       ▼
               localhost:8000
                       │
                       ▼
             FastAPI Container
                       │
        Docker Compose Network
                       │
                       ▼
             Redis Cache Container
```

---

# Docker Concepts Covered

- Docker Compose
- Multi-container applications
- FastAPI in Docker
- Redis Cache
- Docker Networking
- Service Discovery
- Environment Variables
- Health Checks
- Restart Policies
- Cache TTL

---

# Project Structure

```text
06- FastAPI + Redis/
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
│   ├── cache.py
│   ├── dependencies.py
│   ├── settings.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── products.py
│   │
│   ├── models/
│   │   └── product.py
│   │
│   ├── services/
│   │   └── product_service.py
│   │
│   └── static/
│
├── scripts/
│   └── start.sh
│
└── screenshots/
```

---

# Prerequisites

Before running this project, install:

- Docker Desktop (Windows/macOS)
- Docker Engine + Docker Compose (Linux)

No prior Redis knowledge is required.

---

# Project Files

| File | Purpose |
|------|---------|
| Dockerfile | Builds the FastAPI image |
| compose.yaml | Starts FastAPI and Redis |
| cache.py | Creates the Redis connection |
| settings.py | Application configuration |
| product_service.py | Simulates an expensive operation |
| products.py | API endpoints |
| start.sh | Starts Gunicorn with Uvicorn workers |

---

# Architecture Flow

```text
Client

   │

   ▼

GET /products

   │

   ▼

FastAPI

   │

   ▼

Redis Cache

 ┌───────────────┐

 │               │

 ▼               ▼

Hit            Miss

 │               │

 ▼               ▼

Return     Generate Data

                │

                ▼

         Store in Redis

                │

                ▼

         Return Response
```

---

# Quick Start

## 1. Copy Environment Variables

```bash
cp .env.example .env
```

---

## 2. Build the Images

```bash
docker compose build
```

Docker will:

- Read the Dockerfile
- Download dependencies
- Build the FastAPI image

---

## 3. Start the Containers

```bash
docker compose up
```

Docker Compose automatically:

- Creates a Docker network
- Starts Redis
- Performs Redis health checks
- Starts FastAPI

---

## 4. Open the API

```text
http://localhost:8000/products
```

---

## 5. Stop Everything

```bash
docker compose down
```

---

# Cache Demonstration

## First Request

The cache is empty.

```text
Client

↓

Redis

↓

Cache Miss

↓

Generate Data

↓

Wait 5 Seconds

↓

Store in Redis

↓

Return Response
```

Console

```text
Cache miss.

Loading data...
```

---

## Second Request

```text
Client

↓

Redis

↓

Cache Hit

↓

Return Immediately
```

Console

```text
Cache hit.
```

---

# Sample Response

```json
[
  {
    "id": 1,
    "name": "Mechanical Keyboard",
    "price": 99
  },
  {
    "id": 2,
    "name": "Gaming Mouse",
    "price": 49
  },
  {
    "id": 3,
    "name": "Monitor",
    "price": 299
  }
]
```

---

# Docker Compose Services

## api

Responsibilities

- Serves HTTP requests
- Reads from Redis
- Generates data when cache is empty
- Stores responses in Redis

---

## redis

Responsibilities

- Stores cached data
- Expires cache after the configured TTL
- Responds to cache requests

---

# Docker Networking

Docker Compose creates an internal network automatically.

Instead of using:

```text
localhost
```

The FastAPI application connects to Redis using:

```text
redis
```

Docker resolves the hostname internally.

---

# Cache Lifecycle

```text
Application Starts

        │

        ▼

Redis Empty

        │

        ▼

First Request

        │

        ▼

Generate Products

        │

        ▼

Save To Redis

        │

        ▼

Future Requests

        │

        ▼

Read From Cache
```

---

# Environment Variables

The application loads configuration from:

```text
.env
```

Variables:

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

View logs

```bash
docker compose logs
```

View FastAPI logs

```bash
docker compose logs api
```

View Redis logs

```bash
docker compose logs redis
```

Open FastAPI shell

```bash
docker compose exec api sh
```

Open Redis CLI

```bash
docker compose exec redis redis-cli
```

List Redis keys

```bash
KEYS *
```

View cached value

```bash
GET products
```

Delete cache manually

```bash
DEL products
```

Stop containers

```bash
docker compose down
```

---

# What You Learn

| Docker Concept | Where It Appears |
|----------------|------------------|
| Docker Compose | compose.yaml |
| FastAPI Container | api service |
| Redis Container | redis service |
| Redis Cache | cache.py |
| Cache Hit | `/products` endpoint |
| Cache Miss | `product_service.py` |
| Environment Variables | `.env` |
| Docker Networking | Service discovery |
| Health Checks | compose.yaml |
| Restart Policies | compose.yaml |

---

# Common Mistakes

## Wrong Redis Host

Incorrect

```text
localhost
```

Correct

```text
redis
```

---

## Cache Never Expires

Ensure the application uses:

```text
setex()
```

instead of:

```text
set()
```

Otherwise cached data remains indefinitely.

---

## Forgot Environment Variables

Without a valid `.env` file, the application cannot connect to Redis.

---

## Confusing Redis Cache with Redis Database

This project uses Redis **only as a cache**.

It is **not** used as:

- Primary database
- Message broker
- Session store

---

# Best Practices

- Cache expensive operations.
- Keep cache TTL short for frequently changing data.
- Avoid caching everything indiscriminately.
- Use meaningful cache keys.
- Keep Redis in its own container.
- Separate application logic from caching logic.
- Use Docker Compose for local development.

---

# Next Example

The next project introduces **Nginx Reverse Proxy**, demonstrating how Nginx sits in front of backend services to handle incoming HTTP traffic.

---

## Key Takeaways

- Redis dramatically improves response time by serving cached data.
- FastAPI communicates with Redis over Docker's internal network using service names.
- Docker Compose makes it easy to run and manage multiple containers together.
- Cache hits avoid expensive operations, while cache misses populate the cache for future requests.
- Separating caching logic from business logic keeps applications easier to maintain.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*