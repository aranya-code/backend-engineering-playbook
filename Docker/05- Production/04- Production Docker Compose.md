# Production Docker Compose

## Overview

Docker Compose is commonly used during development to run multiple containers together. It can also be used in production for small and medium-sized deployments where a full container orchestration platform is unnecessary.

A production Compose configuration should prioritize stability, security, maintainability, and reproducibility over developer convenience.

Unlike development, production Compose files should avoid bind mounts, debugging configurations, and unnecessary port exposure.

---

# Development vs Production

| Development | Production |
|-------------|------------|
| Source code bind mounts | Immutable Docker images |
| Debugging enabled | Optimized runtime |
| Frequent rebuilds | Versioned releases |
| Local environment | Production infrastructure |
| Convenience | Reliability |
| Open ports | Minimal exposed ports |

---

# Production Architecture

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

                     │

                     ▼

          PostgreSQL Container
```

---

# Example Production Compose File

```yaml
services:

  app:

    image: myapp:1.0.0

    container_name: myapp

    restart: unless-stopped

    expose:
      - "8000"

    env_file:
      - .env.production

    depends_on:

      db:

        condition: service_healthy

    healthcheck:

      test:
        [
          "CMD",
          "curl",
          "-f",
          "http://localhost:8000/health"
        ]

      interval: 30s

      timeout: 5s

      retries: 3

      start_period: 20s

    security_opt:
      - no-new-privileges:true

    mem_limit: 512m

    cpus: 1.0

    pids_limit: 200

    networks:
      - backend


  db:

    image: postgres:17-alpine

    restart: unless-stopped

    environment:

      POSTGRES_DB: appdb

      POSTGRES_USER: appuser

      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

    volumes:

      - postgres_data:/var/lib/postgresql/data

    healthcheck:

      test:
        [
          "CMD-SHELL",
          "pg_isready -U appuser"
        ]

      interval: 10s

      timeout: 5s

      retries: 5

    networks:
      - backend


  nginx:

    image: nginx:1.28-alpine

    restart: unless-stopped

    ports:

      - "80:80"

    depends_on:

      app:

        condition: service_healthy

    volumes:

      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro

    networks:
      - backend


volumes:

  postgres_data:


networks:

  backend:
```

---

# Why Use Images Instead of Build?

Development

```yaml
build: .
```

Production

```yaml
image: myapp:1.0.0
```

Production deployments should use pre-built, versioned images created by the CI/CD pipeline.

---

# Use Restart Policies

Containers should recover automatically after failures.

Recommended

```yaml
restart: unless-stopped
```

Available policies:

| Policy | Description |
|---------|-------------|
| no | Never restart |
| on-failure | Restart after failure |
| always | Always restart |
| unless-stopped | Restart unless manually stopped |

---

# Environment Files

Store configuration outside the Compose file.

Example

```text
.env.production
```

Example contents

```text
APP_ENV=production

DATABASE_HOST=db

DATABASE_PORT=5432
```

Avoid hardcoding configuration values directly into `compose.yaml`.

---

# Secrets

Never commit secrets into source control.

Avoid

```yaml
environment:

  DATABASE_PASSWORD=password123
```

Instead

```yaml
environment:

  DATABASE_PASSWORD=${POSTGRES_PASSWORD}
```

---

# Health Checks

Every critical service should include a health check.

Application

```yaml
healthcheck:

  test:
    [
      "CMD",
      "curl",
      "-f",
      "http://localhost:8000/health"
    ]
```

Database

```yaml
healthcheck:

  test:
    [
      "CMD-SHELL",
      "pg_isready -U appuser"
    ]
```

---

# Service Dependencies

Avoid relying solely on startup order.

Instead use health checks.

```text
Database

↓

Healthy

↓

Application Starts

↓

Healthy

↓

Nginx Starts
```

---

# Resource Limits

Prevent containers from consuming unlimited resources.

```yaml
mem_limit: 512m

cpus: 1.0

pids_limit: 200
```

These values should be adjusted based on workload and available hardware.

---

# Persistent Volumes

Persist important application data.

```yaml
volumes:

  postgres_data:
```

Example

```text
Database

↓

Docker Volume

↓

Persistent Storage
```

Without volumes, database data is lost when the container is removed.

---

# Internal Networking

Docker Compose creates an isolated network.

```text
Internet

↓

Nginx

↓

App

↓

Database
```

Containers communicate using service names rather than IP addresses.

---

# Expose vs Ports

Internal service

```yaml
expose:

  - "8000"
```

Public service

```yaml
ports:

  - "80:80"
```

Only services that must receive external traffic should publish ports.

---

# Logging

Container logs should be written to:

```text
stdout

stderr
```

Docker automatically captures these logs.

---

# Image Versioning

Avoid

```yaml
image: myapp:latest
```

Prefer

```yaml
image: myapp:1.0.0
```

Versioned images simplify deployments and rollbacks.

---

# Production Deployment Flow

```text
Docker Image

↓

Docker Registry

↓

Production Server

↓

Docker Compose

↓

Running Containers
```

---

# Common Mistakes

## Building Images on Production Servers

Avoid

```yaml
build: .
```

Instead deploy pre-built images.

---

## Exposing Databases

Incorrect

```yaml
ports:

  - "5432:5432"
```

Databases should remain private unless remote access is explicitly required.

---

## Missing Restart Policies

Containers should recover automatically after failures.

---

## No Health Checks

Applications without health checks are difficult to monitor and recover automatically.

---

## Using Bind Mounts

Development

```yaml
volumes:

  - ./app:/app
```

Production should rely on immutable images instead of source code bind mounts.

---

# Production Compose Checklist

Before deployment:

- Versioned images
- Restart policies configured
- Health checks enabled
- Resource limits defined
- Secrets externalized
- Volumes configured
- Networks isolated
- Databases not publicly exposed
- Reverse proxy configured
- Environment variables verified

---

# Best Practices

- Deploy immutable, versioned images.
- Use restart policies for resilience.
- Keep secrets outside Compose files.
- Configure health checks for every critical service.
- Limit container resources.
- Store persistent data in Docker volumes.
- Expose only required ports.
- Use service names for container communication.
- Validate the Compose configuration before deployment.

---

# Key Takeaways

- Production Docker Compose focuses on stability, security, and repeatable deployments rather than development convenience.
- Deploy pre-built Docker images instead of building on production servers.
- Health checks, restart policies, and resource limits improve application resilience.
- Environment variables and external secret management keep sensitive information out of source control.
- A well-designed production Compose file provides a reliable foundation for deploying multi-container applications.