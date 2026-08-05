# Production Deployment

## Overview

This project demonstrates how to prepare a Dockerized FastAPI application for **production deployment**.

Unlike previous examples that focused on learning Docker fundamentals, this project applies production-oriented practices such as multi-stage builds, running containers as a non-root user, health checks, environment separation, Nginx reverse proxying, container hardening, and resource limits.

The application remains intentionally simple so the focus stays on deployment architecture rather than application logic.

---

# Project Architecture

```text
                  Internet

                      │

                      ▼

              Nginx Container

                      │

         Docker Compose Network

                      │

                      ▼

            FastAPI Container

               Gunicorn

                    │

             Uvicorn Workers
```

---

# Production Concepts Covered

- Multi-stage Docker Builds
- Production Docker Images
- Gunicorn + Uvicorn
- Nginx Reverse Proxy
- Production Docker Compose
- Environment Separation
- Health Checks
- Restart Policies
- Resource Limits
- Container Hardening
- Non-root Containers
- Security Headers
- Gzip Compression
- Logging
- Production Folder Structure

---

# Project Structure

```text
09- Production Deployment/
│
├── README.md
├── Dockerfile
├── compose.yaml
├── compose.prod.yaml
├── requirements.txt
├── .dockerignore
├── .gitignore
├── .env.example
├── .env.production.example
│
├── app/
│   ├── main.py
│   ├── settings.py
│   │
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
│   ├── start.sh
│   └── healthcheck.sh
│
├── logs/
│   └── .gitkeep
│
├── ssl/
│   ├── README.md
│   └── certificates/
│       └── .gitkeep
│
└── screenshots/
```

---

# Prerequisites

Install:

- Docker Desktop (Windows/macOS)
- Docker Engine + Docker Compose (Linux)

You should already understand:

- Docker Images
- Docker Compose
- Nginx
- FastAPI

---

# Project Files

| File | Purpose |
|------|---------|
| Dockerfile | Multi-stage production image |
| compose.yaml | Development configuration |
| compose.prod.yaml | Production overrides |
| nginx.conf | Global Nginx configuration |
| default.conf | Reverse proxy configuration |
| start.sh | Starts Gunicorn |
| healthcheck.sh | Container health check |
| .env.production.example | Production configuration template |

---

# Development vs Production

| Development | Production |
|-------------|------------|
| Source mounted | Immutable image |
| FastAPI exposed | Behind Nginx |
| `.env` | `.env.production` |
| Convenience | Security |
| Direct debugging | Production deployment |

---

# Application Architecture

```text
Internet

↓

Nginx

↓

Gunicorn

↓

Uvicorn Workers

↓

FastAPI
```

---

# Request Lifecycle

```text
Browser

↓

Nginx

↓

Gunicorn

↓

Worker

↓

FastAPI

↓

JSON Response

↓

Browser
```

---

# Multi-Stage Build

## Builder Stage

Responsible for:

- Installing dependencies
- Building Python packages

---

## Runtime Stage

Contains only:

- Python Runtime
- Installed Packages
- Application Code

This results in a smaller and cleaner production image.

---

# Environment Files

## Development

```text
.env
```

---

## Production

```text
.env.production
```

Production settings remain completely separate from development.

---

# Running Development

## Copy Environment File

```bash
cp .env.example .env
```

---

## Build

```bash
docker compose build
```

---

## Run

```bash
docker compose up
```

Application:

```text
http://localhost:8000
```

---

# Running Production

## Create Production Environment

```bash
cp .env.production.example .env.production
```

---

## Build

```bash
docker compose \
    -f compose.yaml \
    -f compose.prod.yaml \
    build
```

---

## Run

```bash
docker compose \
    -f compose.yaml \
    -f compose.prod.yaml \
    up -d
```

Application:

```text
http://localhost
```

---

# Startup Flow

```text
docker compose up

↓

Build Image

↓

Start FastAPI

↓

Gunicorn

↓

Health Check

↓

Nginx

↓

Ready
```

---

# Gunicorn Architecture

```text
Internet

↓

Gunicorn Master

│

├── Worker 1

├── Worker 2

└── Worker N

↓

FastAPI
```

Gunicorn manages multiple worker processes to handle concurrent requests.

---

# Nginx Responsibilities

Nginx handles:

- Incoming HTTP requests
- Reverse proxying
- Compression
- Security headers
- Connection management

The FastAPI container is never directly exposed.

---

# Health Checks

Docker periodically checks:

```text
/health
```

Healthy

```json
{
    "status": "healthy"
}
```

Unhealthy containers can be restarted automatically.

---

# Container Hardening

This project demonstrates several production security practices:

- Non-root application user
- Read-only Nginx configuration
- Multi-stage build
- Minimal runtime image
- No production secrets in the image
- `no-new-privileges`
- Internal-only application container

---

# Resource Limits

Example:

```yaml
mem_limit: 512m

cpus: 1.0

pids_limit: 200
```

These prevent a single container from consuming unlimited host resources.

---

# Logging

Application logs

```text
stdout

stderr
```

Nginx logs

```text
access.log

error.log
```

Docker collects these logs automatically.

---

# SSL Folder

```text
ssl/

└── certificates/

    ├── fullchain.pem

    └── privkey.pem
```

For this learning project, HTTPS is not configured.

The folder simply demonstrates a production-ready layout.

---

# Useful Commands

Build development image

```bash
docker compose build
```

Build production image

```bash
docker compose \
    -f compose.yaml \
    -f compose.prod.yaml \
    build
```

Run production

```bash
docker compose \
    -f compose.yaml \
    -f compose.prod.yaml \
    up -d
```

View running containers

```bash
docker compose ps
```

View logs

```bash
docker compose logs
```

View API logs

```bash
docker compose logs api
```

View Nginx logs

```bash
docker compose logs nginx
```

Open API shell

```bash
docker compose exec api sh
```

Validate Nginx configuration

```bash
docker compose exec nginx nginx -t
```

Restart services

```bash
docker compose restart
```

Stop services

```bash
docker compose down
```

---

# What You Learn

| Production Concept | Where It Appears |
|--------------------|------------------|
| Multi-stage Build | Dockerfile |
| Gunicorn | start.sh |
| Uvicorn Workers | Gunicorn worker class |
| Reverse Proxy | Nginx |
| Environment Separation | `.env.production` |
| Health Checks | `/health` |
| Restart Policies | Compose |
| Resource Limits | compose.prod.yaml |
| Security Headers | Nginx |
| Non-root User | Dockerfile |
| Container Hardening | Dockerfile + Compose |

---

# Common Mistakes

## Running as Root

Avoid:

```dockerfile
USER root
```

Run the application using an unprivileged user.

---

## Keeping Build Tools

Do not ship compilers and build dependencies inside the runtime image.

Use multi-stage builds.

---

## Hardcoding Secrets

Never store production secrets inside:

```text
Dockerfile

Git Repository
```

Use environment variables instead.

---

## Exposing the Application

Only Nginx should publish ports.

FastAPI should remain internal.

---

## Skipping Health Checks

Always expose a lightweight endpoint such as:

```text
/health
```

This allows Docker and orchestrators to verify application availability.

---

# Best Practices

- Use multi-stage builds.
- Run containers as non-root users.
- Keep development and production configurations separate.
- Store configuration in environment variables.
- Use Nginx as the public entry point.
- Add health checks to every service.
- Keep runtime images as small as possible.
- Avoid committing secrets or certificates to source control.
- Pin image versions for reproducible deployments.

---

# Key Takeaways

- Production Docker deployments require more than a working container—they require secure, maintainable, and reliable configurations.
- Multi-stage builds reduce image size and remove unnecessary build tools from runtime images.
- Gunicorn with Uvicorn workers provides a production-ready process model for FastAPI.
- Nginx acts as the public-facing reverse proxy while the application remains isolated on the internal Docker network.
- Separating development and production Compose files keeps local development simple without compromising deployment practices.
- Health checks, restart policies, environment management, and container hardening are essential parts of a production deployment strategy.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*