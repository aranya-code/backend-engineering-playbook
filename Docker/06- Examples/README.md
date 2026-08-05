# Docker Examples

These hands-on projects complement the conceptual Docker notes in this playbook by demonstrating how Docker is used to build, run, and deploy real backend applications.

Each example introduces one or more Docker concepts and gradually builds toward a complete production-ready CI/CD workflow. The projects are intentionally simple so that the focus remains on understanding Docker, containerization, networking, orchestration, and deployment rather than application complexity.

---

## Quick Navigation

| Project | Description |
|----------|-------------|
| [01- Hello World Container](./01-%20Hello%20World%20Container/) | Build and run your first Docker container. |
| [02- Python Flask](./02-%20Python%20Flask/) | Containerize a simple Flask application. |
| [03- Django PostgreSQL](./03-%20Django%20PostgreSQL/) | Run Django and PostgreSQL with Docker Compose. |
| [04- FastAPI PostgreSQL](./04-%20FastAPI%20PostgreSQL/) | Deploy a FastAPI application with PostgreSQL. |
| [05- Django Redis Celery](./05-%20Django%20Redis%20Celery/) | Add Redis caching and Celery background workers. |
| [06- FastAPI Redis](./06-%20FastAPI%20Redis/) | Improve API performance with Redis caching. |
| [07- Nginx Reverse Proxy](./07-%20Nginx%20Reverse%20Proxy/) | Route requests through an Nginx reverse proxy. |
| [08- Multi Container Application](./08-%20Multi%20Container%20Application/) | Build a complete multi-container backend application. |
| [09- Production Deployment](./09-%20Production%20Deployment/) | Prepare Docker applications for production deployment. |
| [10- CI-CD Deployment](./10-%20CI-CD%20Deployment/) | Automate build, test, and deployment using GitHub Actions. |

---

# Folder Structure

```text
06- Examples/
│
├── 01- Hello World Container/
├── 02- Python Flask/
├── 03- Django PostgreSQL/
├── 04- FastAPI PostgreSQL/
├── 05- Django Redis Celery/
├── 06- FastAPI Redis/
├── 07- Nginx Reverse Proxy/
├── 08- Multi Container Application/
├── 09- Production Deployment/
├── 10- CI-CD Deployment/
└── README.md
```

---

# Learning Progression

```text
Hello World

        │

        ▼

Python Web Application

        │

        ▼

Database Containers

        │

        ▼

Redis

        │

        ▼

Celery

        │

        ▼

Reverse Proxy

        │

        ▼

Multi-Container Applications

        │

        ▼

Production Deployment

        │

        ▼

CI/CD Automation
```

---

# Project Summaries

## 01 – Hello World Container

Build and run your first Docker container while learning the Docker lifecycle, images, containers, and basic Docker commands.

**Topics**

- Docker Images
- Docker Containers
- Docker Build
- Docker Run

---

## 02 – Python Flask

Containerize a lightweight Flask application and expose it through Docker port mapping.

**Topics**

- Python Containers
- Dockerfile
- Port Mapping
- Environment Variables

---

## 03 – Django + PostgreSQL

Run Django and PostgreSQL together using Docker Compose and persistent volumes.

**Topics**

- Docker Compose
- PostgreSQL
- Named Volumes
- Service Discovery

---

## 04 – FastAPI + PostgreSQL

Deploy a FastAPI application backed by PostgreSQL using Docker Compose.

**Topics**

- FastAPI
- PostgreSQL
- Docker Networking
- Health Checks

---

## 05 – Django + Redis + Celery

Introduce asynchronous processing using Redis and Celery.

**Topics**

- Redis
- Celery
- Background Tasks
- Worker Containers

---

## 06 – FastAPI + Redis

Use Redis to cache API responses and improve application performance.

**Topics**

- Redis Cache
- FastAPI
- Cache Hit
- Cache Miss

---

## 07 – Nginx Reverse Proxy

Place Nginx in front of FastAPI to route requests through a reverse proxy.

**Topics**

- Nginx
- Reverse Proxy
- Docker Networking
- Request Routing

---

## 08 – Multi-Container Application

Combine multiple containers into a small backend architecture.

**Topics**

- FastAPI
- Redis
- Celery
- Nginx
- Docker Compose

---

## 09 – Production Deployment

Prepare a Dockerized application for production with Gunicorn, multi-stage builds, health checks, and container hardening.

**Topics**

- Multi-stage Builds
- Gunicorn
- Nginx
- Health Checks
- Production Docker

---

## 10 – CI-CD Deployment

Automate building, testing, and deploying a Docker application using GitHub Actions.

**Topics**

- GitHub Actions
- Continuous Integration
- Continuous Deployment
- Docker Automation
- Deployment Verification

---

# Skills You Will Gain

After completing these projects, you will understand how to:

- Build Docker images
- Create efficient Dockerfiles
- Run and manage containers
- Use Docker Compose
- Connect multiple containers
- Work with PostgreSQL and Redis
- Implement background processing with Celery
- Configure Nginx as a reverse proxy
- Prepare Docker applications for production
- Automate builds and deployments with GitHub Actions

---

# Recommended Order

Complete every project in sequence.

```text
01

↓

02

↓

03

↓

04

↓

05

↓

06

↓

07

↓

08

↓

09

↓

10
```

Each project builds upon the concepts introduced in the previous examples.

---

# Key Takeaways

- The examples progress from basic containers to complete production workflows.
- Each project introduces one or more practical Docker concepts used in real backend systems.
- Docker Compose becomes increasingly important as applications grow beyond a single container.
- Production deployment involves much more than simply running a container—it includes security, health checks, process management, and configuration.
- CI/CD completes the Docker journey by automating the build, test, and deployment lifecycle.