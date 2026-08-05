# Nginx Reverse Proxy

## Overview

This project demonstrates how to place **Nginx** in front of a FastAPI application using **Docker Compose**.

Instead of exposing the application directly to clients, all incoming HTTP requests are first received by Nginx. Nginx then forwards those requests to the FastAPI container over Docker's internal network.

This architecture is commonly used in production environments because it separates public traffic handling from application logic.

The goal of this project is to understand Docker networking, reverse proxies, request forwarding, and multi-container applications.

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
```

---

# Docker Concepts Covered

- Docker Compose
- Multi-container applications
- Reverse Proxy
- Docker Networking
- Service Discovery
- Published vs Exposed Ports
- Environment Variables
- Health Checks
- Gunicorn + Uvicorn
- Request Forwarding

---

# Project Structure

```text
07- Nginx Reverse Proxy/
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
│   ├── routers/
│   │   ├── __init__.py
│   │   └── home.py
│   │
│   └── static/
│
├── nginx/
│   ├── nginx.conf
│   └── default.conf
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

Basic knowledge of Docker containers is recommended.

---

# Project Files

| File | Purpose |
|------|---------|
| Dockerfile | Builds the FastAPI image |
| compose.yaml | Defines the FastAPI and Nginx services |
| nginx.conf | Global Nginx configuration |
| default.conf | Reverse proxy configuration |
| start.sh | Starts Gunicorn with Uvicorn workers |
| main.py | FastAPI application entry point |

---

# Reverse Proxy Flow

```text
Browser

    │

    ▼

localhost:80

    │

    ▼

Nginx

    │

    ▼

FastAPI

    │

    ▼

JSON Response

    │

    ▼

Nginx

    │

    ▼

Browser
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
- Download dependencies
- Build the FastAPI image

---

## 3. Start Containers

```bash
docker compose up
```

Docker Compose automatically:

- Creates a Docker network
- Starts the FastAPI container
- Performs health checks
- Starts the Nginx container

---

## 4. Open the Application

Visit:

```text
http://localhost
```

Notice that the application is accessed through **Nginx**, not directly through FastAPI.

---

## 5. Stop Everything

```bash
docker compose down
```

---

# Expected Output

### Browser

```json
{
    "message": "Hello from FastAPI!",
    "served_by": "FastAPI",
    "hostname": "8d4b91f",
    "python_version": "3.12.11"
}
```

---

### Response Headers

```text
HTTP/1.1 200 OK

Server: nginx

X-Proxy-Server: nginx
```

These headers confirm that the request passed through Nginx.

---

# Docker Compose Services

## api

Responsibilities

- Runs the FastAPI application
- Generates HTTP responses
- Never exposed directly to users

---

## nginx

Responsibilities

- Accepts incoming HTTP requests
- Forwards requests to FastAPI
- Returns responses to clients

---

# Docker Networking

Docker Compose creates an internal network automatically.

The browser communicates only with:

```text
nginx
```

Nginx communicates with:

```text
api
```

The FastAPI container is never exposed publicly.

---

# Published vs Exposed Ports

## Published Port

```yaml
ports:

  - "80:80"
```

Makes the service available outside Docker.

---

## Exposed Port

```yaml
expose:

  - "8000"
```

Makes the service available only to other containers.

---

# Request Lifecycle

```text
Browser

        │

        ▼

HTTP Request

        │

        ▼

Nginx

        │

        ▼

Forward Request

        │

        ▼

FastAPI

        │

        ▼

Generate Response

        │

        ▼

Nginx

        │

        ▼

Browser
```

---

# Health Checks

FastAPI exposes:

```text
/health
```

Docker periodically checks:

```text
http://localhost:8000/health
```

Nginx starts only after FastAPI is healthy.

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

View FastAPI logs

```bash
docker compose logs api
```

View Nginx logs

```bash
docker compose logs nginx
```

Open a shell inside FastAPI

```bash
docker compose exec api sh
```

Open a shell inside Nginx

```bash
docker compose exec nginx sh
```

Validate the Nginx configuration

```bash
docker compose exec nginx nginx -t
```

Reload the Nginx configuration

```bash
docker compose exec nginx nginx -s reload
```

Stop containers

```bash
docker compose down
```

---

# What You Learn

| Concept | Where It Appears |
|----------|------------------|
| Docker Compose | compose.yaml |
| Reverse Proxy | Nginx |
| Request Forwarding | default.conf |
| Docker Networking | Internal Docker Network |
| Service Discovery | `proxy_pass http://api:8000` |
| Published Ports | Nginx |
| Exposed Ports | FastAPI |
| Health Checks | compose.yaml |
| Gunicorn | start.sh |

---

# Common Mistakes

## Using localhost inside Nginx

Incorrect

```text
proxy_pass http://localhost:8000;
```

Correct

```text
proxy_pass http://api:8000;
```

Docker containers communicate using service names.

---

## Exposing FastAPI

Incorrect

```yaml
ports:

  - "8000:8000"
```

Correct

```yaml
expose:

  - "8000"
```

Only Nginx should be publicly accessible.

---

## Editing the Wrong Nginx File

Modify:

```text
default.conf
```

Do not edit the container's internal configuration directly.

---

# Best Practices

- Expose only the reverse proxy to the outside world.
- Keep backend services on Docker's internal network.
- Use service names instead of IP addresses.
- Validate Nginx configuration before reloading.
- Keep application and proxy responsibilities separate.
- Add health checks for backend services.
- Pin Docker image versions.

---

# Next Example

The next project introduces **Multi-Container Application**, combining multiple backend services behind a reverse proxy to demonstrate a more realistic production architecture.

---

## Key Takeaways

- Nginx acts as the single public entry point for the application.
- FastAPI remains private and communicates with Nginx over Docker's internal network.
- Reverse proxies improve security, flexibility, and scalability.
- Docker Compose simplifies managing multiple cooperating containers.
- Separating the proxy layer from the application layer is a common production architecture.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*