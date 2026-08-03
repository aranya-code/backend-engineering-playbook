# Docker Compose

## Overview

Docker Compose is a tool for defining and managing multi-container Docker applications using a single YAML configuration file. Instead of manually starting each container individually, Docker Compose allows developers to define the entire application stack—including services, networks, volumes, environment variables, and dependencies—in one place.

Modern applications rarely consist of a single container. A typical backend application may require a web server, API, database, cache, message broker, and reverse proxy. Docker Compose simplifies managing these interconnected services by allowing the entire application to be started, stopped, and configured using a single command.

Docker Compose is primarily used for local development, testing, CI/CD pipelines, and small-to-medium production deployments.

---

# Why Docker Compose?

Imagine a Django application consisting of:

- Django API
- PostgreSQL
- Redis
- Nginx

Without Docker Compose, each container must be started manually.

```text
docker run nginx

docker run postgres

docker run redis

docker run django
```

Managing dependencies, networking, and startup order quickly becomes difficult.

Docker Compose solves this problem by defining everything in one configuration file.

---

# What is Docker Compose?

Docker Compose is a tool that allows developers to define an entire multi-container application inside a single configuration file.

A Compose project can include:

- Multiple services
- Networks
- Volumes
- Environment variables
- Secrets
- Build configuration
- Health checks

Everything required to run the application is described declaratively.

---

# Docker Compose Architecture

```text
                 Docker Compose

              compose.yaml
                    │
                    ▼
          Docker Compose CLI
                    │
                    ▼
             Docker Engine
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
  API Container  Database     Redis
                 Container   Container
                    │
                    ▼
                Docker Network
                    │
                    ▼
               Docker Volume
```

Docker Compose translates the configuration into Docker resources managed by Docker Engine.

---

# Compose File

Docker Compose uses:

```text
compose.yaml
```

Older projects may still use:

```text
docker-compose.yml
```

Both describe the application's infrastructure.

---

# Basic Compose Structure

A typical Compose file contains:

```yaml
services:

volumes:

networks:
```

Everything begins with the **services** section.

---

# Services

A **service** represents one containerized application.

Example:

```text
services

├── api
├── postgres
├── redis
└── nginx
```

Each service has its own:

- Image
- Environment
- Ports
- Volumes
- Networks
- Restart policy

---

# Example Application

```text
               Internet
                    │
                    ▼
                 Nginx
                    │
                    ▼
              Django API
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     PostgreSQL            Redis
```

Each box represents one Docker Compose service.

---

# Compose Workflow

```text
Application Source Code
          │
          ▼
     compose.yaml
          │
          ▼
 docker compose up
          │
          ▼
 Docker Engine
          │
          ▼
Running Containers
```

Compose automatically creates and manages the required resources.

---

# Networks

Docker Compose automatically creates a dedicated network for the project.

```text
Compose Network

API
 │
 ▼
Redis
 │
 ▼
Database
```

All services can communicate using service names.

Example:

```text
DATABASE_HOST=postgres

REDIS_HOST=redis
```

No IP addresses are required.

---

# Volumes

Compose manages persistent storage.

```text
Docker Volume
      │
      ▼
 PostgreSQL
```

Typical uses:

- Database files
- Uploaded media
- Shared application data
- Logs

Volumes remain after containers are removed.

---

# Environment Variables

Compose simplifies application configuration.

Examples include:

- Database credentials
- API keys
- Debug settings
- Service URLs
- Application configuration

Environment variables can be defined directly or loaded from external files.

---

# Dependency Management

Services often depend on one another.

Example:

```text
API
 │
 ▼
Database
 │
 ▼
Redis
```

Compose allows startup ordering through service dependencies.

However, startup order does **not** guarantee that dependent services are ready to accept connections.

Applications should still implement retry logic or health checks.

---

# Docker Compose Lifecycle

```text
compose.yaml
      │
      ▼
Create Services
      │
      ▼
Create Networks
      │
      ▼
Create Volumes
      │
      ▼
Start Containers
      │
      ▼
Running Application
```

Compose manages the entire application lifecycle.

---

# Compose Project Structure

Typical project:

```text
Project

├── compose.yaml
├── Dockerfile
├── .env
├── requirements.txt
└── application/
```

Compose serves as the entry point for the entire application.

---

# Multi-Container Architecture

```text
                  Browser
                      │
                      ▼
                   Nginx
                      │
                      ▼
                 Django API
                      │
      ┌───────────────┼───────────────┐
      ▼                               ▼
 PostgreSQL                      Redis
                      │
                      ▼
                Docker Volume
```

Docker Compose manages all services together.

---

# Docker Compose in Development

Compose is widely used for:

- Local development
- Integration testing
- Team onboarding
- Feature development
- Automated testing

Developers can reproduce the same environment on any machine.

---

# Docker Compose in CI/CD

Typical workflow:

```text
Git Push
    │
    ▼
CI Pipeline
    │
    ▼
Build Images
    │
    ▼
Docker Compose
    │
    ▼
Run Integration Tests
```

Compose enables reliable testing using production-like environments.

---

# Production Considerations

Docker Compose works well for:

- Small deployments
- Internal tools
- Development environments
- Proof-of-concept applications

For large-scale production environments requiring:

- Auto scaling
- Multi-host deployments
- Self-healing
- Advanced scheduling
- Automatic failover

An orchestration platform such as Docker Swarm or Kubernetes is generally more appropriate.

---

# Advantages

Docker Compose provides:

- Declarative infrastructure
- One-command application startup
- Automatic networking
- Persistent storage management
- Environment consistency
- Easy onboarding
- Reproducible deployments

---

# Limitations

Docker Compose has some limitations.

- Single-host focused
- Limited orchestration capabilities
- No built-in auto scaling
- Limited self-healing
- Not designed for very large distributed systems

---

# Common Misconceptions

### Docker Compose replaces Kubernetes.

Incorrect.

Docker Compose manages multi-container applications on a single host, while Kubernetes orchestrates containerized workloads across clusters.

---

### Docker Compose creates one container.

Incorrect.

A Compose project usually creates multiple containers.

---

### Compose automatically waits until databases are ready.

Incorrect.

Compose controls startup order but applications should still perform readiness checks.

---

# Best Practices

- Keep one service per container.
- Use named volumes for persistent data.
- Store configuration in environment variables.
- Use service names instead of IP addresses.
- Keep Compose files modular and readable.
- Pin image versions.
- Add health checks where appropriate.
- Separate development and production configurations when necessary.

---

# Related Topics

- Docker Containers
- Docker Networking
- Docker Volumes
- Dockerfile
- Docker Swarm
- Docker Best Practices

---

## Key Takeaways

- Docker Compose simplifies the deployment and management of multi-container applications using a declarative YAML configuration.
- Services, networks, volumes, and environment variables are defined in a single Compose file, enabling reproducible environments.
- Compose automatically creates project-specific networks and manages container dependencies and persistent storage.
- It is an excellent tool for development, testing, and small-to-medium deployments but is not a replacement for full container orchestration platforms.
- Understanding Docker Compose is essential for building modern backend applications that rely on multiple interconnected services.